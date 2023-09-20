# -*- coding: utf-8 -*-
{
    'name': "AZ Portal Contact Attachment",
    'summary': """
        Enable customer to attach files on contact card via portal
        """,
        
    'description': """
        Enable customer to attach files on contact card via portal
    """,
    
    'author': "Azkatech SAL",
    'website': "http://www.azka.tech",
    'category': 'Website',
    'version': '15.0.0.0',
    "license": "AGPL-3",
    "support": "odoo@azka.tech",
    
    'depends': ['base','website', 'portal'],
    
    'data': [
        'views/attachment.xml',
        'views/portal_templates.xml'

    ],
    
    'assets': {
       
        'web.assets_frontend': [
            'az_portal_contact_attachments/static/src/js/az_portal_contact_attachment.js',
            'az_portal_contact_attachments/static/src/js/bootbox.min.js',
                
        ],
       
    },
    
    
    'application': False,
    'images': ['static/description/banner.png'],
}