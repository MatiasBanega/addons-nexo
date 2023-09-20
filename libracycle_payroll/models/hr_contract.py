from odoo import models, fields, api


class HRContract(models.Model):
    _inherit = 'hr.contract'

    loan_deduction = fields.Float(string="Loan Deduction")
    other_deduction = fields.Float(string="Other Deduction")
    cooperative = fields.Float(string="Cooperative")
    advance_deduction = fields.Float(string="Advance Deduction")


   