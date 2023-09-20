# -*- coding: utf-8 -*-

{
    'name': 'Employees Competences Views',
    'author': 'Odoopedia',
    'version': '16.0',
    'category': 'Human Resources',
    'sequence': 85,
    'summary': """Employee education
                  Employees education
                  Employees qualifications
                  Employee qualifications
                  Educational background
                  Professional development
                  Training and certifications
                  Learning and development
                  Qualifications and skills
                  Employee learning records
                  Employee competency 
                  Employees competency
                  Employee learning records
                  Employees learning records
                  Competency development
                  Work history
                  Employment record
                  Career progression
                  Job responsibilities
                  Professional achievements
                  Relevant experience
                  Skill set
                  Work experience
                  Job performance
                  Career development
                  Job duties
                  Workload management
                  Employee productivity
                  Performance appraisal
                  Job satisfaction""",
    'maintainer': 'Odoopedia',
    'website': 'https://www.odoopedia.com',
    'description': """
        This module adds a valuable addition to the existing functionality of the Odoo HR module.
        By displaying the employee's education and experience in separate tree views, a more comprehensive views of an employee's qualifications, skills and work history will be provided.""",
    'license': 'OPL-1',
    'support': 'contact@odoopedia.com',
    'depends': ['hr', 'hr_skills'],
    'data': [
        'views/hr_employee_views.xml',
    ],
    'images': ['static/description/banner.gif'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
