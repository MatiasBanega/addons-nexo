# -*- coding: utf-8 -*-
{
    'name': "AZ Mindspace Vendor Portal",
    'summary': """
        AZ Mindspace Vendor Portal
        """,
        
    'description': """
       AZ Mindspace Vendor Portal
    """,
    
    'author': "Azkatech SAL",
    'website': "http://www.azka.tech",
    'category': 'Website',
    'version': '15.0.0.0',
    "license": "AGPL-3",
    "support": "odoo@azka.tech",
    
    'depends': ['purchase','website'],
    
    'data': [
        'security/ir.model.access.csv',
        'data/mail_activity_type.xml',
        'views/purchase_portal_templates.xml',
        'views/purchase_inherited.xml',
        'views/res_config_settings_views.xml',
    ],
    
    'assets': {
       
        'web.assets_frontend': [
                'az_mindspace_vendor_portal/static/src/js/az_vendor_portal.js',
                'az_mindspace_vendor_portal/static/src/js/bootbox.min.js',

            ],
    },
    
    'application': False,
    'images': ['static/description/banner.png'],
}