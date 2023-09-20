from odoo import models, fields

class DocumentFolder(models.Model):
    _inherit = "documents.folder"
    
    is_crm_folder = fields.Boolean("CRM Main Folder")
    crm_customer_id = fields.Many2one("res.partner", string="CRM Customer")
    crm_lead_id = fields.Many2one("crm.lead", string="CRM Opportunity")
    is_subfolder = fields.Boolean()