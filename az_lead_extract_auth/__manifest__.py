

{
     'name': "LinkedIn leads extractor",
   'summary': """
        Reads the LinkedIn contact and create an Odoo lead in a single click
        """,

    'description': """
       Reads the LinkedIn contact and create an Odoo lead in a single click
    """,
    
    'author': "Azkatech SAL",
    'website': "http://www.azka.tech",
    'version': '15.0.0.0.0',
    "category": "CRM",
    "license": "AGPL-3",
    "support": "support+odoo@azka.tech",
    
    'price': 10,
    'currency': 'USD',
    
    'depends': ['base', 'web', 'crm'],
    
    'data': [
         'security/ir.model.access.csv',
        'views/res_config_settings.xml',
        'views/token.xml',
        'data/cron.xml',
    ],
    
    
    'installable': True,
   
    'images': ['static/description/banner.png'],
   
}
