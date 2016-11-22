# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Skrill Payment Acquirer',
    'category': 'Payment Acquirer',
    'summary': 'Payment Acquirer: Skrill Implementation',
    'description': """
    Skrill Payment Acquirer for India.

    Skrill payment gateway supports only INR currency.
    """,
    'depends': ['payment'],
    'data': [
        'views/payment_views.xml',
        'views/payment_skrill_templates.xml',
        'data/payment_acquirer_data.xml',
    ],
    'license': 'OEEL-1',
}
