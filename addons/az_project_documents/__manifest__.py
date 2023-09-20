# See LICENSE file for full copyright and licensing details.

{
    'name': 'Save Project Attachments in Documents App',
    'version': '15.0.1.0.0',
    'category': 'Productivity/Documents',
    'author': 'Azkatech',
    'website': 'https://azka.tech',
    'license': 'LGPL-3',
    'price': 10,
    'currency': 'USD',
    'support': 'support+apps@azka.tech',
    'maintainer': 'Azkatech',
    'summary': 'Ability to add the attachments of Project/Tasks to the'
               'Documents App in a customized way determined in configuration settings.',
    'depends': [
        'base','documents','documents_project'
    ],
    'data': [
        'views/res_config_settings.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
}

