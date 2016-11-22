# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint
import werkzeug

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class SkrillController(http.Controller):
    @http.route(['/payment/skrill/return',], type='http', auth='none')
    def skrill_return(self, **post):
        '''Payment Skrill Return'''
        _logger.info('Beginning Skrill form_feedback with post data %s', pprint.pformat(post)) # debug
        request.env['payment.transaction'].sudo().form_feedback(post, 'skrill')
        return werkzeug.utils.redirect('/shop/payment/validate')

    
    @http.route(['/payment/skrill/cancel', '/payment/skrill/error'], type='http', auth='public', csrf=False)
    def skrill_cancel(self, **post):
        """ Skrill."""
        _logger.info(
            'Skrill: entering form_feedback with post data %s', pprint.pformat(post))
        return_url = '/'
        if post:
            request.env['payment.transaction'].sudo().form_feedback(post, 'skrill')
            return_url = post.get('udf1')
        return werkzeug.utils.redirect(return_url)
