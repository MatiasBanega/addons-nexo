from odoo import _, api, fields, models

class HrExpense(models.Model):
    _inherit = "hr.expense"
    _rec_name = 'lbc_name'

    lbc_name = fields.Char()

    @api.model
    def create(self, vals):
        res = super(HrExpense, self).create(vals)
        return res

  