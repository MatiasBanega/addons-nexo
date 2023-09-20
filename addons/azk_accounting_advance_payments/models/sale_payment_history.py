from odoo import api, fields, models

class SalePaymentHistory(models.Model):
    _name = 'sale.payment.history'
    _description = 'Sale Advance Payment History'
    
    payment_id = fields.Many2one('account.payment')
    payment_status = fields.Selection(related="payment_id.state")
    order_id = fields.Many2one('sale.order', string="Sale Order")
    name = fields.Char(related="payment_id.name", string="Name", readonly=True)
    journal_id = fields.Many2one(related="payment_id.journal_id", string="Payment (Journal)", readonly=True)
    payment_date = fields.Date(related="payment_id.date", string="Payment Date", readonly=True)
    advance_amount = fields.Monetary(related="payment_id.amount", required=True)
    payment_amount_main_currency = fields.Monetary(related="payment_id.payment_amount_main_currency")
    currency_id = fields.Many2one(related="payment_id.currency_id", string="Payment Currency", readonly=True)
    partner_id = fields.Many2one(related="payment_id.partner_id", string="Partner")
    payment_method_id = fields.Many2one(related="payment_id.payment_method_id", string="Payment Method", readonly=True)
    total_amount = fields.Float(string="Total Amount", readonly=True)
    currency_rate = fields.Float(compute="_compute_currency_rate", string="Currency Rate", readonly=True)
    company_currency_id = fields.Many2one(related="order_id.company_id.currency_id", readonly=True)
    
    @api.depends('advance_amount', 'payment_amount_main_currency')
    def _compute_currency_rate(self):
        for record in self:
            record.currency_rate = (record.advance_amount / (record.payment_amount_main_currency or 1)) if (not record.payment_id.apply_manual_currency_exchange) else record.payment_id.manual_currency_exchange_rate