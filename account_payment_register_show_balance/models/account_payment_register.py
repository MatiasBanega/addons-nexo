from odoo import api, fields, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    journal_balance = fields.Float(
        string="Account Balance", compute="_compute_journal_balance"
    )

    @api.depends("journal_id")
    def _compute_journal_balance(self):
        for rec in self:
            rec.journal_balance = -1 * rec.journal_id.default_account_id.current_balance
