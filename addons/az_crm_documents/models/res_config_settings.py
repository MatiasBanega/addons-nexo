from odoo import models, fields

_STRUCTURES = [
    ("single_folder", "Flat (One Folder For all Opportunity)"),
    ("by_customer", "By Customer"),
    ("by_opportunity", "By Opportunity"),
    ("by_customer_oppurtunity", "By Customer/Opportunity")
]

class ResCompany(models.Model):
    _inherit = "res.company"
    
    documents_crm_settings = fields.Boolean("CRM")
    add_attachments_as_document = fields.Boolean()
    crm_workspace_structure = fields.Selection(selection=_STRUCTURES, string="Workspace Structure")

class Attachment(models.TransientModel):
    _inherit = "res.config.settings"
    
    documents_crm_settings = fields.Boolean(related="company_id.documents_crm_settings", readonly=False)
    add_attachments_as_document = fields.Boolean(related="company_id.add_attachments_as_document", readonly=False)
    crm_workspace_structure = fields.Selection(related="company_id.crm_workspace_structure", readonly=False)