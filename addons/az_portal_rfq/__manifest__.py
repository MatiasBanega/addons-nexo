# -*- coding: utf-8 -*-
{
    'name': "AZ Portal RFQ",
    'summary': """
        Enable vendor to add price to rfq in his portal page
        """,
        
    'description': """
       Enable vendor to add price to rfq in his portal page
    """,
    
    'author': "Azkatech SAL",
    'website': "http://www.azka.tech",
    'category': 'Website',
    'version': '15.0.0.0',
    "license": "AGPL-3",
    "support": "odoo@azka.tech",
    
    'depends': ['purchase','website'],
    
    'data': [
        'views/purchase_portal_templates.xml',
        'views/purchase_inherited.xml',
        'data/mail_activity_type.xml',
    ],
    
    'assets': {
       
        'web.assets_frontend': [
                'az_portal_rfq/static/src/js/az_portal_rfq.js',
                'az_portal_rfq/static/src/js/bootbox.min.js',
#                 'azk_instagram_feed/static/src/css/insta_feed_style.css',
            ],
    },
    
    'application': False,
    'images': ['static/description/banner.png'],
}