# -*- coding: utf-8 -*-
{
    'name': "AZ Vendor Portal Rating",
    'summary': """
       AZ Vendor Portal Rating
        """,
        
    'description': """
       AZ Vendor Portal Rating
    """,
    
    'author': "Azkatech SAL",
    'website': "http://www.azka.tech",
    'category': 'Website',
    'version': '15.0.0.0',
    "license": "AGPL-3",
    "support": "odoo@azka.tech",
    
    'depends': ['base','purchase', 'portal', 'website'],
    
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_portal_templates.xml',
        'views/vendor_rating.xml',
    ],
    
    'assets': {
        
        'web.assets_frontend': [
                'az_vendor_rating_portal/static/src/js/chart.min.js',
                'az_vendor_rating_portal/static/src/js/az_vendor_rating_portal.js',

            ],
    },
    
    'application': False,
    'images': ['static/description/banner.png'],
}