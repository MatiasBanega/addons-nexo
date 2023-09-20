# See LICENSE file for full copyright and licensing details.

{
    'name': 'Save CRM Attachments in Documents',
    'version': '15.0.1.0.1',
    'category': 'Sales',
    'author': 'Azkatech',
    'website': 'https://azka.tech',
    'license': 'LGPL-3',
    'price': 10,
    'currency': 'USD',
    'support': 'support+apps@azka.tech',
    'maintainer': 'Azkatech',
    'summary': 'Automatically save all the attachments found in the chatter of the CRM, from log notes and emails to the documents app',
    'depends': [
        'base','documents','crm'
    ],
    'data': [
        'views/res_config_settings.xml',
        'views/documents_folder.xml',
        'wizards/mail_compose_message.xml',
        'wizards/add_document_wizard_view.xml',
        'security/ir.model.access.csv'
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
}

