# -*- coding: utf-8 -*-
{
    "name": "Conector Odoo - BNA",
    'version': '10.0.1.0.0',
    'category': 'Localization/Argentina',
    'sequence': 14,
    'author': 'Moldeo Interactive,Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'summary': '',
    'depends': [
        'base','account'
    ],
    'data': [
        'data/cron.xml',
        'data/data.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
