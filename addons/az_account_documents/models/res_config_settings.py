from odoo import models, fields

ACCOUNT_DOCS_STRUCTURES = [
    ("by_entry", "By Journal Entry"),
    ("by_journal_entry", "By Journal/Journal Entry"),
]

class ResCompany(models.Model):
    _inherit = "res.company"
    
    use_specific_structure = fields.Boolean(string="Use Customized structure For Accounting documents", default=False)
    account_documents_structure = fields.Selection(selection=ACCOUNT_DOCS_STRUCTURES, string="Folders Structure to Follow")

    def write(self, vals):
        use_specific_structure = False
        if vals.get('use_specific_structure') and vals.get('use_specific_structure') == True:
            use_specific_structure = True
        res = super().write(vals)
        if use_specific_structure:
            # deleting records of accounting folders structure settings if we want to use
            # the customized on in the module
            self.env["documents.account.folder.setting"].search([]).unlink()
        return res

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"
    
    use_specific_structure = fields.Boolean(related="company_id.use_specific_structure", readonly=False)
    account_documents_structure = fields.Selection(related="company_id.account_documents_structure", readonly=False)
