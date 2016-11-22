# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import hashlib
import urlparse

from odoo import api, fields, models, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.tools.float_utils import float_compare

import logging

_logger = logging.getLogger(__name__)


class PaymentAcquirerSkrill(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('skrill', 'Skrill')])
    skrill_merchant_key = fields.Char(string='Merchant Key', required_if_provider='skrill', groups='base.group_user')
    skrill_merchant_salt = fields.Char(string='Merchant Salt', required_if_provider='skrill', groups='base.group_user')

    def _get_skrill_urls(self, environment):
        """ Skrill URLs"""
        if environment == 'prod':
            return {'skrill_form_url': 'https://pay.skrill.com'}
        else:
            return {'skrill_form_url': 'https://pay.skrill.com'}

    def _skrill_generate_sign(self, values):
        """ Generate the shasign for incoming or outgoing communications.
        :param self: the self browse record. It should have a shakey in shakey out
        :param dict values: transaction values

        :return string: sha2sig
        """
        sign = self.skrill_merchant_salt + values.get('transaction_id') + self.skrill_merchant_key

        shasign = hashlib.sha512(sign).hexdigest()
        return shasign

    @api.multi
    def skrill_form_generate_values(self, values):
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        skrill_values = dict(values,
                             pay_to_email='demoqco@sun-fish.com',
                             currency='USD',
                             prepare_only=1,
                                key=self.skrill_merchant_key,
                                transaction_id=values['reference'],
                                amount=values['amount'],
                                productinfo=values['reference'],
                                firstname=values.get('partner_name'),
                                email=values.get('partner_email'),
                                phone=values.get('partner_phone'),
                                service_provider='skrill_paisa',
                                surl='%s' % urlparse.urljoin(base_url, '/payment/skrill/return?transaction_id=%s' % (values['reference'])),
                                furl='%s' % urlparse.urljoin(base_url, '/payment/skrill/error?transaction_id=%s' % (values['reference'])),
                                curl='%s' % urlparse.urljoin(base_url, '/payment/skrill/cancel?transaction_id=%s' % (values['reference'])),
                                )
        skrill_values['udf1'] = skrill_values.pop('return_url', '/')
        skrill_values['sha2sig'] = self._skrill_generate_sign(skrill_values)
        return skrill_values

    @api.multi
    def skrill_get_form_action_url(self):
        self.ensure_one()
        return self._get_skrill_urls(self.environment)['skrill_form_url']


class PaymentTransactionSkrill(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def _skrill_form_get_tx_from_data(self, data):
        """ Given a data dict coming from skrill, verify it and find the related
        transaction record. """
        reference = data.get('transaction_id')
        pay_id = data.get('mihpayid')
        shasign = data.get('hash')
        if not reference: # or not pay_id or not shasign:
            raise ValidationError(_('Skrill: received data with missing reference (%s) or pay_id (%s) or shashign (%s)') % (reference, pay_id, shasign))

        transaction = self.search([('reference', '=', reference)])

        if not transaction:
            error_msg = (_('Skrill: received data for reference %s; no order found') % (reference))
            raise ValidationError(error_msg)
        elif len(transaction) > 1:
            error_msg = (_('Skrill: received data for reference %s; multiple orders found') % (reference))
            raise ValidationError(error_msg)

        #verify shasign
        #shasign_check = '1234' # transaction.acquirer_id._skrill_generate_sign('out', data)
        #if shasign_check.upper() != shasign.upper():
        #    raise ValidationError(_('Skrill: invalid shasign, received %s, computed %s, for data %s') % (shasign, shasign_check, data))
        return transaction

    @api.multi
    def _skrill_form_get_invalid_parameters(self, data):
        invalid_parameters = []

        return invalid_parameters

    @api.multi
    def _skrill_form_validate(self, data):
        # status = data.get('status')
        transaction_status = {
            'success': {
                'state': 'done',
                'acquirer_reference': data.get('skrillId'),
                'date_validate': fields.Datetime.now(),
            },
            'pending': {
                'state': 'pending',
                'acquirer_reference': data.get('skrillId'),
                'date_validate': fields.Datetime.now(),
            },
            'failure': {
                'state': 'cancel',
                'acquirer_reference': data.get('skrillId'),
                'date_validate': fields.Datetime.now(),
            },
            'error': {
                'state': 'error',
                'state_message': data.get('error_Message') or _('Skrill: feedback error'),
                'acquirer_reference': data.get('skrillId'),
                'date_validate': fields.Datetime.now(),
            }
        }
        vals = transaction_status.get('success', False)
        if not vals:
            vals = transaction_status['error']
            _logger.info(vals['state_message'])
        return self.write(vals)
