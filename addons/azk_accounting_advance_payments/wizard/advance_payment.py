from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

log = logging.getLogger(__name__)

class AdvancePayment(models.TransientModel):
    _name = 'advance.payment'
    _description = "Advance Payment"

    name = fields.Char(string="Origin", readonly=True)
    journal_id = fields.Many2one('account.journal', string='Payment (Journal)', required=True, domain=[('type', 'in',['bank','cash'])])
    payment_date = fields.Date(string="Payment Date")
    total_amount = fields.Float(string="Total Amount", readonly=True)
    advance_amount = fields.Monetary(string='Payment Amount', required=True)
    account_amount = fields.Float('Account Amount', help='Amount to be recorded in the SOA')
    account_currency_id = fields.Many2one('res.currency', 'Account Currency', help='Account Currency', default=lambda self: self.env.company.currency_id)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.user.company_id.currency_id)
    company_id = fields.Many2one('res.company', related='journal_id.company_id', string='Company', readonly=True)
    partner_id = fields.Many2one('res.partner', string="Partner")
    

    payment_method_line_id = fields.Many2one('account.payment.method.line', string='Payment Method',
        readonly=False, store=True, copy=False,
        compute='_compute_payment_method_line_id',
        domain="[('id', 'in', available_payment_method_line_ids)]",
        help="Manual: Pay or Get paid by any method outside of Odoo.\n"
        "Payment Acquirers: Each payment acquirer has its own Payment Method. Request a transaction on/to a card thanks to a payment token saved by the partner when buying or subscribing online.\n"
        "Check: Pay bills by check and print it from Odoo.\n"
        "Batch Deposit: Collect several customer checks at once generating and submitting a batch deposit to your bank. Module account_batch_payment is necessary.\n"
        "SEPA Credit Transfer: Pay in the SEPA zone by submitting a SEPA Credit Transfer file to your bank. Module account_sepa is necessary.\n"
        "SEPA Direct Debit: Get paid in the SEPA zone thanks to a mandate your partner will have granted to you. Module account_sepa is necessary.\n")
    available_payment_method_line_ids = fields.Many2many('account.payment.method.line',
        compute='_compute_payment_method_line_fields')
    hide_payment_method_line = fields.Boolean(
        compute='_compute_payment_method_line_fields',
        help="Technical field used to hide the payment method if the selected journal has only one available which is 'manual'")
    payment_method_id = fields.Many2one(
        related='payment_method_line_id.payment_method_id',
        string="Method",
        tracking=True,
        store=True
    )


    payment_type = fields.Selection([('outbound', 'Send Money'), ('inbound', 'Receive Money')], string='Payment Type')
    paid_payment = fields.Monetary(compute='_compute_advance_amount_diff', readonly=True, store=True)
    
    purchase_id = fields.Many2one('purchase.order', string="PO")
    
    sale_id = fields.Many2one('sale.order', string="Name")
    residual_currency_id = fields.Many2one('res.currency', string='Currency')
    currency_rate = fields.Float(string="Currency Rate", readonly=True)
    payment_method_code = fields.Char(related='payment_method_id.code',
        help="Technical field used to adapt the interface to the payment type selected.", readonly=True)
    ref = fields.Char(string="Memo")
    note = fields.Char(string="Note")
    bank_link = fields.Many2one('res.bank', string="Bank")
    due_date = fields.Date(string='Due Date', help="The date at which the check should be issued")
    collection_date = fields.Date(string='Collection Date', track_visibility='always', help="The date at which the check should be collected")
    check_number = fields.Char()
    check_amount_in_words = fields.Char(string="Amount in Words")
    apply_manual_currency_exchange = fields.Boolean(string='Apply Manual Currency Exchange')
    manual_currency_exchange_rate = fields.Float(string='Manual Currency Exchange Rate')
    active_manual_currency_rate = fields.Boolean('Active Manual Currency', default=False)
    amount_tax = fields.Monetary('Amount Tax')
    
    @api.onchange('advance_amount', 'journal_id')
    def _onchange_amount(self):
        self.check_amount_in_words = self.currency_id.amount_to_text(self.advance_amount) if self.currency_id else False
        
    @api.onchange('account_amount', 'currency_id')
    def _onchange_currency(self):        
        self.advance_amount = self.account_currency_id._convert(self.account_amount, self.currency_id, self.company_id, fields.date.today())
    
    def _get_payment_method_codes_to_exclude(self):
        # can be overriden to exclude payment methods based on the payment characteristics
        self.ensure_one()
        return []
    
    @api.depends('available_payment_method_line_ids')
    def _compute_payment_method_line_id(self):
        ''' Compute the 'payment_method_line_id' field.
        This field is not computed in '_compute_payment_method_line_fields' because it's a stored editable one.
        '''
        for pay in self:
            available_payment_method_lines = pay.available_payment_method_line_ids

            # Select the first available one by default.
            if pay.payment_method_line_id in available_payment_method_lines:
                pay.payment_method_line_id = pay.payment_method_line_id
            elif available_payment_method_lines:
                pay.payment_method_line_id = available_payment_method_lines[0]._origin
            else:
                pay.payment_method_line_id = False
    
    @api.depends('payment_type', 'journal_id')
    def _compute_payment_method_line_fields(self):
        for pay in self:
            pay.available_payment_method_line_ids = pay.journal_id._get_available_payment_method_lines(pay.payment_type)
            to_exclude = pay._get_payment_method_codes_to_exclude()
            if to_exclude:
                pay.available_payment_method_line_ids = pay.available_payment_method_line_ids.filtered(lambda x: x.code not in to_exclude)
            if pay.payment_method_line_id.id not in pay.available_payment_method_line_ids.ids:
                # In some cases, we could be linked to a payment method line that has been unlinked from the journal.
                # In such cases, we want to show it on the payment.
                pay.hide_payment_method_line = False
            else:
                pay.hide_payment_method_line = len(pay.available_payment_method_line_ids) == 1 and pay.available_payment_method_line_ids.code == 'manual'
                
    @api.depends('advance_amount', 'payment_date', 'currency_id')
    def _compute_advance_amount_diff(self):

        active_id = self._context.get('active_id')
        if self.sale_id:
            active_model = self.env['sale.order'].browse(active_id)
        else:
            active_model= self.env['purchase.order'].browse(active_id)
            
        if len(active_model.payment_history_ids) == 0:
            return
        
        for record in self:
            record.paid_payment = record.get_total_paid_amount()

    def get_total_paid_amount(self):
        """ Compute the sum of the residual of invoices, expressed in the payment currency """
        total = 0
        journal_id = self.env['account.journal'].search([('type', 'in', ['bank', 'cash'])], limit=1)
        payment_currency = self.env['res.currency'].browse(self._context.get('currency_id')) or journal_id.currency_id or journal_id.company_id.currency_id or self.env.user.company_id.currency_id
        active_id = self._context.get('active_id')
        if self._context.get('sale_id'):
            active_model_id = self.env['sale.order'].browse(active_id)
        else:
            active_model_id = self.env['purchase.order'].browse(active_id)
        for pay in active_model_id.payment_history_ids:
            if not pay.currency_id or pay.currency_id.id == payment_currency:
                total += pay.advance_amount
            else:
                total += pay.currency_id._convert(pay.advance_amount, payment_currency, active_model_id.company_id, fields.Date.today())
    
        return abs(total)

    @api.model
    def default_get(self,default_fields):
        res = super(AdvancePayment, self).default_get(default_fields)
        context = self._context
        payment_data = {'name': context.get('name'), 
                        'currency_id': context.get('currency_id'), 
                        'account_currency_id': context.get('currency_id'), 
                        'total_amount': context.get('total_amount'), 
                        'currency_rate': context.get('currency_rate'), 
                        'payment_date': fields.Date.today(), 
                        'company_id': context.get('company_id'), 
                        'amount_tax': context.get('amount_tax'), 
                        'sale_id': context.get('sale_id'), 
                        'purchase_id': context.get('purchase_id'), 
                        'partner_id': context.get('partner_id'),
                        'advance_amount': context.get('total_amount') - self.get_total_paid_amount(),
                        'account_amount': context.get('total_amount') - self.get_total_paid_amount(),
                        'ref': context.get('ref'),
                        'journal_id': self.env['account.journal'].search([('type', 'in', ['bank', 'cash'])], limit=1).id,
                        }
        if context.get('sale_id'):
            payment_data.update({'payment_type':'inbound'})
        else:
            payment_data.update({'payment_type':'outbound'})
        res.update(payment_data)
        
        return res

    @api.onchange('payment_type')
    def _onchange_payment_type(self):
        if self.payment_type:
            return {'domain': 
                        {'payment_method_id': [('payment_type', '=', self.payment_type)]}
                    }

    def generate_advance_payment(self):
        if self.sale_id:
            if not self.partner_id.prepayment_receivable_id or not self.partner_id.prepayment_vat_receivable_id:
                raise ValidationError(_('Configure Partner Pre-Payment accounts'))
            
            elif self.total_amount - self.paid_payment < self.account_amount or self.account_amount <= 0.00 or self.advance_amount <= 0.00:
                raise ValidationError(_('Enter a valid advance payment amount.'))
        else:
            if not self.partner_id.prepayment_payable_id or not self.partner_id.prepayment_vat_payable_id:
                raise ValidationError(_('Configure Partner Pre-Payment accounts'))
            remained_amount = self.account_currency_id._convert(self.total_amount - self.paid_payment, self.currency_id, self.company_id, fields.date.today())
            if remained_amount < self.advance_amount or self.advance_amount <= 0.00:
                raise ValidationError(_('Enter a valid advance payment amount.'))
        
        payment_data = {'payment_type':'inbound' if self.sale_id else 'outbound',
                        'partner_type':'customer' if self.sale_id else 'supplier', 
                        'partner_id': self.partner_id.id,
                        'amount': self.advance_amount, 
                        'journal_id': self.journal_id.id, 
                        'date': self.payment_date, 
                        'ref': self.ref if self.sale_id else self.purchase_id.name,
                        'note': self.note,
                        'payment_method_id':self.payment_method_id.id, 
                        'order_id': self.sale_id.id if self.sale_id else None,
                        'purchase_id': self.purchase_id.id if self.purchase_id else None,
                        'currency_id':self.currency_id.id,
                        'bank_link': self.bank_link.id,
                        'due_date': self.due_date,
                        'collection_date': self.collection_date,
                        'check_number': self.check_number,
                        'check_amount_in_words': self.check_amount_in_words,
                        'manual_currency_exchange_rate': 1,
                        'active_manual_currency_rate': False,
                        'apply_manual_currency_exchange': False,
                        'advance_payment': True
                        }
        payment_fields = self.env['account.payment']._fields
        if 'account_amount' in payment_fields:
            payment_data['account_amount'] = self.account_amount
        if 'account_currency_id' in payment_fields:
            payment_data['account_currency_id'] = self.account_currency_id.id
        if 'company_currency_id' in payment_fields:
            payment_data['company_currency_id'] = self.journal_id.company_id.currency_id.id
        if 'invoice_total_amount' in payment_fields:
            payment_data['invoice_total_amount'] = self.total_amount
        

        res = self.env['account.payment'].create(payment_data)
        res.action_post()
        
        self.write({'name': res.name})
                   
        if res.state == 'posted':
            if self.sale_id:
                self.sale_id.write({'payment_history_ids': [(0,0,{'payment_id':res.id,
                                                                   'currency_rate':self.currency_rate,
                                                                   'total_amount':self.total_amount,
                                                                   })
                                                            ]})
            else:
                self.purchase_id.write({'payment_history_ids': [(0, 0, {'name': self.name,
                                                                        'payment_id': res.id,
                                                                        'payment_date': self.payment_date,
                                                                        'partner_id': self.partner_id.id,
                                                                        'journal_id': self.journal_id.id,
                                                                        'payment_method_id': self.payment_method_id.id,
                                                                        'currency_id': self.currency_id.id,
                                                                        'advance_amount': self.advance_amount,
                                                                        'total_amount': self.total_amount
                                                                        })
                                                                ]})
                
        action_vals = {
            'name': _('Advance Payment'),
            'domain': [('id', 'in', res.ids), ('state', '=', 'posted')],
            'view_type': 'form',
            'res_model': 'account.payment',
            'view_id': False,
            'type': 'ir.actions.act_window',
        }

        if len(res) == 1:
            action_vals.update({'res_id': res[0].id, 'view_mode': 'form'})
            
        return action_vals