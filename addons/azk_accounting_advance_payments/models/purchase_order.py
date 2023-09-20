from odoo import fields, models, _,api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    payment_history_ids = fields.One2many('purchase.payment.history','purchase_id', 
                                            string="Advance Payment Information", 
                                            domain=[('payment_status','!=','cancelled')])
    payments_amount = fields.Monetary(compute="_compute_payments_amount", string='Payments Amount', copy=False) 
    payments_percentage = fields.Float(compute="_compute_payments_amount", string='Payments %', copy=False)
                                        

    def set_advance_payment(self):
        pay_wiz_data = {}
        view_id = self.env.ref('azk_accounting_advance_payments.purchase_advance_payment_wizard')
        if view_id:
            pay_wiz_data={
                'name' : _('Purchase Advance Payment'),
                'type' : 'ir.actions.act_window',
                'view_type' : 'form',
                'view_mode' : 'form',
                'res_model' : 'advance.payment',
                'view_id' : view_id.id,
                'target' : 'new',
                'context' : {'name':self.name,
                            'purchase_id':self.id,
                            'total_amount':self.amount_total,
                            'company_id':self.company_id.id,
                            'currency_id':self.currency_id.id,
                            'date_order':self.date_order,
                            'partner_id':self.partner_id.id,
                            },
            }
            
        return pay_wiz_data
    @api.depends('payment_history_ids.payment_amount_main_currency')
    def _compute_payments_amount(self):
        """
        Get all payments related to the sales order and sum the payments amount
        """
        for record in self:
            record.payments_amount = record.company_id.currency_id._convert(sum(record.payment_history_ids.mapped('payment_amount_main_currency')), 
                                                                     record.pricelist_id.currency_id, record.company_id, record.validity_date or fields.Date.today())
            record.payments_percentage = round( (record.payments_amount / (record.amount_total or 1)) * 100 , 2)
             
    
    def _prepare_invoice(self):
        result = super(PurchaseOrder, self)._prepare_invoice()
        default_advance_payment_moves = []
        for history in self.payment_history_ids:
            default_advance_payment_moves.append(history.payment_id.move_id.id)
        result['advance_payment_moves'] = default_advance_payment_moves
      
        return result 