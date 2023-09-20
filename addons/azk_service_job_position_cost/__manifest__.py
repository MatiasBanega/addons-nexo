{
    'name': "Service Job Position Cost",

    'summary': "  Calculate the job position hourly cost and reflect the cost on the similar service",

    'description': "  ",
    
    'author': "Azkatech",
    'website': "http://www.azka.tech",
    'license': 'AGPL-3',
    'support': "support+apps@azka.tech",
    'version': '15.0.0.0.0',
    'application': False,
    'depends': ['base','sale','hr_timesheet','product','hr_contract'],

    'data': [
            'views/product_template.xml',
            'views/settings.xml',
            'views/company.xml',
  
    ],
   
}
