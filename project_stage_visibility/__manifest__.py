{
    'name': 'Project Stage Visibility',
    'version': '1.0',
    'summary': 'Hide project stages based on user',
    'description': 'This module allows you to hide or show project stages based on user',
    'category': 'Project',
    'author': 'Caleb Royer',
    'depends': ['project'],
    'data': [
        'security/ir.model.access.csv',
        'views/project_stage_visibility_views.xml',
    ],
    'installable': True,
    'application': False,  
    'auto_install': False,
}
