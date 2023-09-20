{
    "name": "Leave Approvers",
    "version": "15.0.1.0.0",
    "summary": """Leave Approvers""",
    "description": "Leave Approvers",
    "category": "Generic Modules/Human Resources",
    "depends": ["base_setup", "hr_holidays"],
    "data": [
        "views/hr_leave.xml",
        "data/mail_template.xml",
        "security/ir.model.access.csv",
        "security/security.xml",
    ],
    "images": ["static/description/banner.png"],
    "license": "AGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
}
