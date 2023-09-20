from odoo import models, fields

PROJECT_DOCS_STRUCTURES = [
    ("by_project", "By Project"),
    ("by_project_task", "By Project/Task"),
    ("by_customer_project", "By Customer/Project"),
    ("by_customer_project_task", "By Customer/Project/Task")
]

class ResCompany(models.Model):
    _inherit = "res.company"
    
    project_documents_structure = fields.Selection(selection=PROJECT_DOCS_STRUCTURES, string="Folders Structure to Follow")

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"
    
    project_documents_structure = fields.Selection(related="company_id.project_documents_structure", readonly=False)
