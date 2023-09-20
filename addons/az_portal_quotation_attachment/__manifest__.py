# -*- coding: utf-8 -*-
{
    'name': "AZ Portal Quotation Attachment",
    'summary': """
        Enable customer to attach file when signing the quotation
        """,
        
    'description': """
       Enable customer to attach file when signing the quotation
    """,
    
    'author': "Azkatech SAL",
    'website': "http://www.azka.tech",
    'category': 'Website',
    'version': '15.0.0.0',
    "license": "AGPL-3",
    "support": "odoo@azka.tech",
    
    'depends': ['sale','website', 'portal'],
    
    'data': [
        'views/res_config_settings_views.xml',

    ],
    
    'assets': {
       
        'web.assets_frontend': [
            'az_portal_quotation_attachment/static/src/js/az_portal_quatation_attachment.js',
            'az_portal_quotation_attachment/static/src/js/az_portal_composer.js',
                
        ],
        'web.assets_qweb': [
            'az_portal_quotation_attachment/static/src/xml/portal_signature_inherited.xml',
        ],
    },
    
    'application': False,
    'images': ['static/description/banner.png'],
}