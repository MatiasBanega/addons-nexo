
{
    "name": "eyk attendance auto checkout",
    'author': 'Forcefx at Github',
    'website': 'https://github.com/Forcefx/eyk_attendance_auto_checkout',
    "version": "15.0.2",
    'category': 'Attendances',
    'summary': """Automatically check out the employee based on
                  maximum hours set in the ui and optional send Email to a specific address""",            
    'depends': ['hr_attendance'],
    'data': [
        'data/scheduler.xml',
        'views/attendance_settings_view.xml',
    ],
    'license': 'Other proprietary',
    'installable': True,
    'application': True,
    'auto_install': False,
}
