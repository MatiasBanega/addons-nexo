# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.

{
    'name': 'Employee Appraisals Process and Evaluation Form',
    'version': '1.1.1',
    'price': 99.0,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'category': 'Human Resources/Employees',
    'summary': 'Employee Appraisals Process and Evaluation Form',
    'depends': ['hr', 'calendar'],
    'description': """
This app allows your HR / Evaluation Team to do the employee appraisal
evaluation as shown the below screenshots.
""",
    'author': 'Probuse Consulting Service Pvt. Ltd.',
    'website': 'http://www.probuse.com',
    'support': 'contact@probuse.com',
    'images': ['static/description/e.png'],
    'live_test_url': 'https://probuseappdemo.com/probuse_apps/odoo_hr_evaluation_form/1287',
    "data": [
        'security/hr_evaluation_security.xml',
        'security/ir.model.access.csv',
        'data/evaluation_email_template.xml',
        'data/evaluation_data.xml',
        'wizard/next_appraisal_date_view.xml',
        'wizard/evaluator_generator.xml',
        'views/hr_evaluation_view.xml',
        'views/menu_actions.xml',
        'views/hr_evaluation_installer.xml',
        'views/report_evaluation_perormance.xml',
        'views/evaluation_performance_view.xml',
        'views/evaluation_performance_template_views.xml',
        'views/competencies_bjectives_view.xml',
        'views/rating_view.xml',
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
