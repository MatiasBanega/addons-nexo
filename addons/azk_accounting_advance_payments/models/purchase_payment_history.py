from odoo import fields, models

class PurchasePaymentHistory(models.Model):
    _name = 'purchase.payment.history'
    _description = 'Purchase Advance Payment History'

    purchase_id = fields.Many2one('purchase.order', string="Purchase")
    payment_id = fields.Many2one('account.payment')
    payment_status = fields.Selection(related="purchase_id.state")
    name = fields.Char(string="Name", readonly=True)
    journal_id = fields.Many2one('account.journal', string="Payment (Journal)", readonly=True)
    payment_date = fields.Datetime(string="Payment Date", readonly=True)
    total_amount = fields.Float(string="Total Amount", readonly=True)
    advance_amount = fields.Monetary(string="Advance Paid Amount", readonly=True)
    currency_id = fields.Many2one('res.currency', string="Payment Currency", readonly=True)
    partner_id = fields.Many2one('res.partner', string="Partner")
    payment_method_id = fields.Many2one('account.payment.method', string="Payment Method", readonly=True)
    payment_amount_main_currency = fields.Monetary(related="payment_id.payment_amount_main_currency")
    currency_rate = fields.Float(compute="_compute_currency_rate", string="Currency Rate", readonly=True)
    company_currency_id = fields.Many2one(related="purchase_id.company_id.currency_id", readonly=True)