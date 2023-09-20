# See LICENSE file for full copyright and licensing details.

{
    'name': 'Save Accounting Attachments in Documents App',
    'version': '15.0.1.0.1',
    'category': 'Productivity/Documents',
    'author': 'Azkatech',
    'website': 'https://azka.tech',
    'license': 'LGPL-3',
    'price': 10,
    'currency': 'USD',
    'support': 'support+apps@azka.tech',
    'maintainer': 'Azkatech',
    'summary': 'Ability to add the attachments of Accounting Journals/Entries to the'
               'Documents App in a customized way determined from configuration settings.',
    'depends': [
        'base','documents','documents_account'
    ],
    'data': [
        'views/res_config_settings.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
}

