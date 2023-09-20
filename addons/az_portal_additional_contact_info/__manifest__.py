# -*- coding: utf-8 -*-
{
    'name': "AZ Portal Additional Contact Info",
    'summary': """
        AZ Portal Additional Contact Info
        """,
        
    'description': """
      AZ Portal Additional Contact Info
    """,
    
    'author': "Azkatech SAL",
    'website': "http://www.azka.tech",
    'category': 'Website',
    'version': '15.0.0.0',
    "license": "AGPL-3",
    "support": "odoo@azka.tech",
    
    'depends': ['website', 'portal'],
    
    'data': [
        'views/portal_templates.xml',

    ],
    
   
    
    'application': False,
    'images': ['static/description/banner.png'],
}