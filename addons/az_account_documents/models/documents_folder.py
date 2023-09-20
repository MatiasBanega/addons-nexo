from odoo import models, fields, api

class DocumentFolder(models.Model):
    _inherit = "documents.folder"
    
    journal_id = fields.Many2one("account.journal", string="Journal")
    journal_entry_id = fields.Many2one("account.move", string="Journal Entry")