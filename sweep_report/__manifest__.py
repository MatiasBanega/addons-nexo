{
    'name': 'Sweep Report',
    'version': '2.4',
    'summary': 'Print the xlsx report of sweep entries with date interval of your choice',
    'description':
        """
        This module helps to print the xlsx report of sweep entries with date interval of your choice.
        """,
    'category': 'Reporting',
    'author': 'MOB - Hamza Ilyas',
    'website': 'hamza.ilyaaaas@gmail.com',
    'depends': ['base', 'report_xlsx', 'sweep'],
    'data': [
        # 'data/scheduler.xml',
        'security/ir.model.access.csv',
        # 'wizard/sweep_process_wizard.xml',
        'wizard/sweep_report_wizard.xml',
        'views/sweep_report_main.xml',
        # 'views/view.xml',
        # 'views/credit_application_sequence.xml',
    ],
    "license": "LGPL-3",
    'installable': True,
    'auto_install': False,
}
