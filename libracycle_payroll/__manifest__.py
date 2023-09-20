{
    'name': "Libracycle Payroll",
    'summary': """Libracycle Payroll Customization""",
    'description': """Libracycle Payroll Customization""",
    'author': "Matt O'Bell",
    'website': "https://www.mattobell.net",
    'category': 'Uncategorized',
    'version': '1.1',
    'depends': ['base', 'hr_payroll'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/hr_contract.xml',
        'views/hr_payslip.xml',

    ],

    'license': 'LGPL-3'
}
