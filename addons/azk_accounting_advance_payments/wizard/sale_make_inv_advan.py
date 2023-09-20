from odoo import models, fields, api,_
from odoo.exceptions import Warning
import logging

log = logging.getLogger(__name__)

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def create_invoices(self):
        res = super(SaleAdvancePaymentInv, self).create_invoices()
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        for order in sale_orders:
            for history in order.payment_history_ids:
                for invoice in order.invoice_ids:
                    invoice.advance_payment_moves = [(4, history.payment_id.move_id.id)]
                    
        return res