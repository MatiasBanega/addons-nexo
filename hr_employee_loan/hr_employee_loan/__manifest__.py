# -*- encoding: utf-8 -*-

{
    "name": "Loan Management By Employee",
    "version": "15.0.0.0.2",
    "description": """
        Split journal into parts if split is ticked while processing payslip
    """,
    'author': "Matt O'Bell Ltd",
    'category': 'Human Resources/Payroll',
    "depends": [
       'hr_payroll',
       'payroll_accounting_extension',
    ],
    "data": [
        "views/account_move.xml",
        "views/hr_salary_rule_views.xml",
    ],

    "installable": True,
    "auto_install": True,
}
