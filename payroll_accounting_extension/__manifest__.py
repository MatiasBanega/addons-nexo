# -*- coding: utf-8 -*-
# Iheb Ltaief.

{
    'name': 'Payroll Accounting Extension',
    'version': '15.0.0.0',
    'category': 'Human Resources/Payroll',
    'summary': 'This Module add an option in the rule if you want to be linked with the related partner and add the analytic account with only expense accounts',
    'description': """
    - You can easily choose the rule that you want to be linked with partner. 
    - Analytic account related with rules by default will be linked with all your journal entry lines but with this module it will be linked only with expenses accounts.
    """,
    'price': 0,
    'currency': "USD",
    'author': 'Iheb Ltaief',
    'website': 'ihebltaief@gmail.com',
    'depends': ['hr_payroll_account'],
    'data': ["views/hr_rule.xml"],
    'support': 'ihebltaief@gmail.com',
    'installable': True,
    'auto_install': False,
    'application': True,
    'images': ['static/description/banner.png'],
    "live_test_url":'https://youtu.be/-W_djlVW14o',
    'license': 'OPL-1',
}
