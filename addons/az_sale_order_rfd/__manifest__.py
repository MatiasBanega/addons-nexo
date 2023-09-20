# -*- coding: utf-8 -*-
{
    'name': "AZ Sale Order Request For Delivery",
    'summary': """
        Ability to Request a Delivery for a sales order to be sent to the customer and request his action approve/reject on the delivery files.
    """,
    'description': """
    """,
    'author': "Azkatech",
    'website': "http://www.azka.tech",
    'category': 'Sales',
    'version': '15.0.0.0.0',
    "license": "AGPL-3",
    "support": "odoo@azka.tech",
    'depends': ['sale_management','website', 'portal', 'survey', 'project', 'crm'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        
        'views/request_for_delivery.xml',
        'views/sale_order.xml',
        'views/sale_order_portal.xml',
        
        'wizards/upload_file_wizard.xml',

    ],
    'assets': {
        'web.assets_frontend': [
            'az_sale_order_rfd/static/src/js/az_sale_order_rfq.js',
        ],
    },
    'application': False,
}