# -*- coding: utf-8 -*-
{
    'name': "AZ Proposal Order",
    'summary': """
        AZ Proposal Order
        """,
        
    'description': """
       AZ Proposal Order
    """,
    
    'author': "Azkatech SAL",
    'website': "http://www.azka.tech",
    'category': 'Sale',
    'version': '15.0.0.0',
    "license": "AGPL-3",
    "support": "odoo@azka.tech",
    
    'depends': ['base', 'sale_management', 'portal', 'account'],
    
    'data': [
        'security/ir.model.access.csv',
        'security/access_groups.xml',
        'data/porposal_stages.xml',
        'data/proposal_mail_template.xml',
        'views/proposal.xml',
        'views/propodal_portal_templates.xml',

    ],
    
   
    'application': False,
    'images': ['static/description/banner.png'],
}