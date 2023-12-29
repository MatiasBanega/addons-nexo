# -*- coding: utf-8 -*-
{
    'name': 'Nexo Notification',
    'version': '1',
    'summary': 'Nexo Notification',
    'sequence': -103,
    'description': """Nexo Notification""",
    'license': 'AGPL-3',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
        # 'views/views.xml'
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'assets': {
        'web.assets_backend': [
            'notification/static/src/js/notification.js',
        ],
    }
}
