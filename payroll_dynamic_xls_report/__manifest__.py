{
    'name': 'payroll report excel (engine)',
    'version': '15.0',
    'category': 'payroll',
    'sequence': 60,
    'summary': 'Dynamic Payroll Report Excel',
    'description': "It shows payroll report in excel for given month,create your own report",
    'author':'Agile Solutions',
    'website': 'www.agileitsolution.com',
    'depends': ['base','hr', 'hr_payroll'],
    'data': [
        'security/ir.model.access.csv',
        'views/payroll_report.xml',
        'wizard/payroll_report_wiz.xml'
      ],
    'images': ['static/description/cover.png'],
    'auto_install': False,
    'installable': True,
    'application': True,
    'price': 35,
    'currency': 'USD',
    'support': 'apps@agileitsolution.com',
}
