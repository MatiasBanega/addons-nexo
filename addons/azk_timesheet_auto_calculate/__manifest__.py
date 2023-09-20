{
    'name': "TimeSheet Auto Calculate",
    'summary': " Calculate the employee's hourly cost based on his salary",
    'description': "Calculate the employee's hourly cost based on his salary",
    'author': "Azkatech",
    'website': "https://www.azka.tech",
    'license': 'AGPL-3',
    'support': "support+apps@azka.tech",
    'version': '15.0.0.0.1',
    'application': False,
    'depends': ['base', 'hr_contract', 'hr_payroll', 'hr', 'hr_timesheet'],
    'data': [
        'views/company.xml',
        'views/contract.xml',
        'views/settings.xml',
        'views/employee.xml',
    ],
   
}
