from odoo import models, fields, api

class DocumentFolder(models.Model):
    _inherit = "documents.folder"
    
    project_id = fields.Many2one("project.project", string="Project")
    project_customer_id = fields.Many2one("res.partner", string="Project Customer")
    project_task_id = fields.Many2one("project.task", string="Project Task")