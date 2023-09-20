# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.

{
    "name": "Employee Advance Salary Requests",
    "version": "5.5.1",
    "price": 49.0,
    "currency": "EUR",
    "license": "Other proprietary",
    # 'live_test_url': 'https://youtu.be/foSt6CHlrgA',
    "live_test_url": "https://probuseappdemo.com/probuse_apps/employee_advance_salary/891",  #'https://youtu.be/WJ0c0AXXr0E',
    "category": "Human Resources",
    "summary": "Employee Advance Salary Requests and Workflow - Integrated with Accounting",
    "description": """
Employee Advance Salary Requests:
Employee advance salary
Employee advance salary request
            """,
    "author": "Probuse Consulting Service Pvt. Ltd.",
    "website": "www.probuse.com",
    "depends": ["hr", "account", "hr_payroll"],
    "images": ["static/description/img2.jpg"],
    "data": [
        "security/employee_advance_salary_security.xml",
        "security/ir.model.access.csv",
        # 'data/salary_rule_data.xml',
        "views/employee_advance_salary.xml",
        "views/hr_job.xml",
        "report/employee_advance_salary_report.xml",
    ],
    "demo": ["data/salary_rule_data.xml"],
    "installable": True,
    "application": False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
