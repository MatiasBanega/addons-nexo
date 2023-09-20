from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    analytic_account_id = fields.Many2one('account.analytic.account')

    def action_create_payments(self):
        payments = self._create_payments()

        if self.analytic_account_id:
            for pmt in payments:
                pmt.analytic_account_id = self.analytic_account_id
                pmt.payment_difference = self.payment_difference

        if self._context.get('dont_redirect_to_payments'):
            return True

        action = {
            'name': _('Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'context': {'create': False},
        }
        if len(payments) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': payments.id,
            })
        else:
            action.update({
                'view_mode': 'tree,form',
                'domain': [('id', 'in', payments.ids)],
            })
        return action


class AccountPayment(models.Model):
    _inherit = "account.payment"

    analytic_account_id = fields.Many2one('account.analytic.account')
    payment_difference = fields.Monetary()

