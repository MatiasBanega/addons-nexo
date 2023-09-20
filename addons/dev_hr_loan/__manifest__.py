# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle 
#
##############################################################################


{
    'name': 'Employee Loan Management, HR Loan Process Employee',
    'version': '15.0.1.2',
    'sequence': 1,
    'category': 'Generic Modules/Human Resources',
    'description':
        """
odod Apps will add Hr Employee Loan functioality for employee
        
Employee loan management
Odoo employee loan management
HR employee loan
Odoo HR employee loan
HR loan for employee
HR loan approval functionality 
Loan Installment link with employee payslip
Loan notification employee Inbox
Loan Deduction in employee payslip
Manage employee loan 
Manage employee loan odoo
Manage HR loan for employee
Manage HR loan for employee odoo
Loan management 
Odoo loan management
Odoo loan management system
Odoo loan management app
helps you to create customized loan
 module allow HR department to manage loan of employees
Loan Request and Approval
Odoo Loan Report
create different types of loan for employees
allow user to configure loan given to employee will be interest payable or not.
Open HRMS Loan Management
Loan accounting
Odoo loan accounting
Employee can create loan request.
Manage Employee Loan and Integrated with Payroll 

odoo app Loan functionality for employee | employee loan Integrated with Payroll | HR employee loan management employee salary deduction for loan amount  | loan amount easy deduction in employee payslip | Manage employee loan | HR loan for employee | Odoo loan management | Loan Request and Approval

    """,
    'summary': 'odoo app Loan functionality for employee | employee loan Integrated with Payroll | HR employee loan management employee salary deduction for loan amount  | loan amount easy deduction in employee payslip | Manage employee loan | HR loan for employee | Odoo loan management | Loan Request and Approval',
    'depends': ['hr_payroll','account'],
#    hr_payroll_account
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'report/employee_loan_template.xml',
        'report/report_menu.xml',
        'views/loan_emi_view.xml',
        'views/hr_employee_view.xml',
        'views/hr_loan_view.xml',
        'views/ir_sequence_data.xml',
        'views/employee_loan_type_views.xml',
        'edi/mail_template.xml',
        'edi/skip_installment_mail_template.xml',
        'views/pay_slip_view.xml',
        'views/salary_structure.xml',
        'wizard/import_loan_views.xml',
        'wizard/import_logs_view.xml',
        'views/dev_skip_installment.xml',
        'views/hr_loan_dashbord.xml',
        'views/loan_document.xml',
        'views/loan_report_views.xml',
        ],
    'demo': [],
    'test': [],
    'css': [],
    'qweb': [],
    'js': [],
    'images': ['images/main_screenshot.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    
    # author and support Details =============#
    'author': 'DevIntelle Consulting Service Pvt.Ltd',
    'website': 'http://www.devintellecs.com',    
    'maintainer': 'DevIntelle Consulting Service Pvt.Ltd', 
    'support': 'devintelle@gmail.com',
    'price':45.0,
    'currency':'EUR',
    #'live_test_url':'https://youtu.be/A5kEBboAh_k',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
