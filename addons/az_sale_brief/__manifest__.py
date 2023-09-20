# -*- coding: utf-8 -*-
{
    'name': "AZ Sale Brief",
    'summary': """
       AZ Sale Brief
        """,
        
    'description': """
       AZ Sale Brief
    """,
    
    'author': "Azkatech SAL",
    'website': "http://www.azka.tech",
    'category': 'sale',
    'version': '15.0.0.0',
    "license": "AGPL-3",
    "support": "odoo@azka.tech",
    
    'depends': ['sale','website_sale', 'portal', 'sale_management'],
    
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/brief_mail_template.xml',
        'views/brief.xml',
        'views/brief_portal_templates.xml',

    ],
    
    'assets': {
        
        'web.assets_frontend': [
                 'az_sale_brief/static/src/js/summernote.min.js',
                  'az_sale_brief/static/src/js/summernote.min.css',
                'az_sale_brief/static/src/js/az_brief.js',
                'az_sale_brief/static/src/js/bootbox.min.js',
            ],
    },
    
    'application': False,
    'images': ['static/description/banner.png'],
}