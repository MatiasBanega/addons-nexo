{
    "name": "LBC Employee Advance Salary Requests",
    "version": "1.0.2",

    "license": "Other proprietary",
    "category": "Human Resources",
    "summary": "Employee Advance Salary Requests and Workflow - Integrated with Accounting",
    "description": """Employee Advance Salary Requests and Workflow - Integrated with Accounting""",
    "author": "Probuse Consulting Service Pvt. Ltd.",
    "website": "www.probuse.com",
    "depends": ["employee_advance_salary", "libracycle_process_workflow"],
    "data": [
        # "security/employee_advance_salary_security.xml",
        "data/mail_template.xml",
        "views/employee_advance_salary.xml",
    ],
    "installable": True,
    "application": False,
}
