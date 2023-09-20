from odoo import api, fields, models, _
import logging
from odoo.exceptions import ValidationError

log = logging.getLogger(__name__)

class AccountPayment(models.Model):
    _inherit = 'account.payment'
    
    order_id = fields.Many2one('sale.order', copy=False)
    advance_payment_move = fields.Many2one('account.move' , copy=False)
    advance_payment_reversal = fields.Many2one('account.payment', copy=False)
    purchase_id = fields.Many2one('purchase.order', copy=False)
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Company Currency", readonly=True)
    payment_amount_main_currency = fields.Monetary(currency_field='company_currency_id', store=True, readonly=True, compute='_compute_amount')
    note = fields.Char(string="Note")
    bank_link = fields.Many2one('res.bank', string="Bank")
    due_date = fields.Date(string='Due Date', help="The date at which the check should be issued")
    apply_manual_currency_exchange = fields.Boolean(string='Apply Manual Currency Exchange')
    manual_currency_exchange_rate = fields.Float(string='Manual Currency Exchange Rate')
    active_manual_currency_rate = fields.Boolean('Active Manual Currency', default=False)
    collection_date = fields.Date(string='Collection Date', track_visibility='always', help="The date at which the check should be collected")
    advance_payment = fields.Boolean('Advance Payment')
    advance_payment_vat = fields.Many2one('account.tax')
    
    
    def create_reverse_payment(self):
        payment_data = {'payment_type': self.payment_type,
                        'partner_type':self.partner_type, 
                        'partner_id': self.partner_id.id,
                        'amount': self.amount, 
                        'journal_id': self.journal_id.id, 
                        'date': fields.Date.today(), 
                        'ref': self.ref,
                        'note': self.note,
                        'payment_method_id':self.payment_method_id and self.payment_method_id.id or False, 
                        'currency_id':self.currency_id and self.currency_id.id or False,
                        'bank_link': self.bank_link and self.bank_link.id or False,
                        'due_date': self.due_date,
                        'check_number': self.check_number,
                        }
        res = self.env['account.payment'].create(payment_data)
        res.action_post()
        return res

    
    def _prepare_default_reversal_advanced(self, move):
        return {
            'ref': _('Reversal of: Advance Payment'),
            'date': fields.Date.today(),
            'invoice_date': False,
            'journal_id': move.journal_id.id,
            'invoice_payment_term_id': None,
            'auto_post': True,
            'invoice_user_id':False,
        }
    
    @api.depends('amount', 'currency_id', 'company_id', 'date')
    def _compute_amount(self):
        """
        Convert to main currency the amount
        """
        for record in self:
            if record.apply_manual_currency_exchange and record.manual_currency_exchange_rate:
                record.payment_amount_main_currency = (record.amount / record.manual_currency_exchange_rate) if record.manual_currency_exchange_rate > 0 else record.amount_total
            else:
                record.payment_amount_main_currency = record.currency_id._convert(record.amount,record.company_currency_id, record.company_id, record.date or fields.Date.today())

    def decrease_tax_value(self, old_val, tax_percent):
        if not old_val:
            return old_val, 0.0
        tax_val = tax_percent * old_val
        new_val = old_val - tax_val
        return new_val, tax_val
    
    def action_draft(self):
        res = super().action_draft()
        if self.advance_payment_reversal:
             raise ValidationError(_("You cannot reset the advance payment reversed"))
        return res
    
    def reverse_advanced_payment(self):
        default_values_list = []
        default_values_list.append(self._prepare_default_reversal_advanced(self.move_id))

        batches = [
            [self.env['account.move'], [], True],   # Moves to be cancelled by the reverses.
            [self.env['account.move'], [], False],  # Others.
        ]
        for move, default_vals in zip(self.move_id, default_values_list):
            is_auto_post = True
            is_cancel_needed = not is_auto_post 
            batch_index = 0 if is_cancel_needed else 1
            batches[batch_index][0] |= move
            batches[batch_index][1].append(default_vals)

        # Handle reverse method.
        moves_to_redirect = self.env['account.move']
        for moves, default_values_list, is_cancel_needed in batches:
            new_moves = moves._reverse_moves(default_values_list, cancel=is_cancel_needed)                
            
        new_moves.action_post()        
        self.advance_payment_move = new_moves
        self.advance_payment_reversal = self.create_reverse_payment()

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        all_move_vals = super()._prepare_move_line_default_vals(write_off_line_vals)
        pre_receive = self.partner_id.prepayment_receivable_id or (self.partner_id.parent_id.prepayment_receivable_id if self.partner_id.parent_id else False)
        pre_receive_vat = self.partner_id.prepayment_vat_receivable_id or (self.partner_id.parent_id.prepayment_vat_receivable_id if self.partner_id.parent_id else False)
        pre_payable = self.partner_id.prepayment_payable_id or (self.partner_id.parent_id.prepayment_payable_id if self.partner_id.parent_id else False)
        pre_payable_vat = self.partner_id.prepayment_vat_payable_id or (self.partner_id.parent_id.prepayment_vat_payable_id if self.partner_id.parent_id else False)
        if self.advance_payment:
            if (not pre_receive or not pre_receive_vat)  and self.payment_type == 'inbound':
                raise ValidationError(_('Configure Partner Pre-Payment accounts'))
            if (not pre_payable or not pre_payable_vat)  and self.payment_type == 'outbound':
                raise ValidationError(_('Configure Partner Pre-Payment accounts'))
        company_currency = self.company_id.currency_id
        for line in all_move_vals:
            if self.advance_payment:
                if self.order_id:
                    account_id = self.partner_id.property_account_receivable_id.id
                    prepayment_account = pre_receive
                    amount_total = self.order_id.amount_total
                    amount_tax = self.order_id.amount_tax
                    prepayment_tax_account = pre_receive_vat if amount_tax > 0.0 else None
                    order_currency_id = self.order_id.pricelist_id.currency_id
                    field_name = 'credit'
                elif self.purchase_id:
                    account_id = self.partner_id.property_account_payable_id.id
                    prepayment_account = pre_payable
                    amount_total = self.purchase_id.amount_total
                    amount_tax = self.purchase_id.amount_tax
                    prepayment_tax_account = pre_payable_vat if amount_tax > 0.0 else None
                    order_currency_id = self.purchase_id.currency_id
                    field_name = 'debit'
                else:
                    order_currency_id = self.currency_id
                    prepayment_tax_account = pre_payable_vat if self.payment_type != 'inbound'  else pre_receive_vat
                    
                if self.purchase_id or self.order_id:
                    rate = self.manual_currency_exchange_rate if self.apply_manual_currency_exchange else order_currency_id.rate


                    if  order_currency_id != self.company_currency_id:
                        order_rate = rate if order_currency_id == self.currency_id else order_currency_id.rate
                        amount_total = amount_total / order_rate
                        amount_tax = amount_tax / order_rate
                
                vat_amount_currency = 0.0
                new_currency_id = None
                vat_amount = 0.0
                if self.purchase_id or self.order_id:
                    amount_untaxed = amount_total - amount_tax
                
                if line['account_id'] == self.partner_id.property_account_receivable_id.id or line['account_id'] == self.partner_id.property_account_payable_id.id:
                    if (self.payment_type =='inbound' and pre_receive.id ) or ( self.payment_type == 'outbound' and pre_payable.id):
                        line['account_id'] = self.payment_type =='inbound' and pre_receive.id or pre_payable.id
                if (self.purchase_id or self.order_id) and ((pre_receive and pre_receive.id ==  line['account_id']) or  (pre_payable and line['account_id'] == pre_payable.id)):

                    if line[field_name]:
                        tmp_vat_amount_currency = False
                        vat_amount_currency = 0
                        percentage = (amount_total - amount_untaxed) / amount_total
                        if 'amount_currency' in line:
                            line['amount_currency'], tmp_vat_amount_currency = self.decrease_tax_value(line['amount_currency'], percentage)
                        line[field_name], vat_amount = self.decrease_tax_value(line[field_name], percentage)
                        if 'amount_currency' in line and line['amount_currency'] != 0:
                            vat_amount = self.env['res.currency'].browse(line['currency_id'])._convert(tmp_vat_amount_currency, self.company_id.currency_id, self.company_id, fields.Date.today())
                        
                        if order_currency_id != company_currency:
                            if tmp_vat_amount_currency:
                                vat_amount_currency = tmp_vat_amount_currency
                            new_currency_id = order_currency_id
                if self.advance_payment_vat and ((pre_receive and pre_receive.id ==  line['account_id']) or  (pre_payable and line['account_id'] == pre_payable.id)):
                    field_name = self.payment_type == 'outbound' and 'debit' or 'credit'
                    
                    if line[field_name]:
                        tmp_vat_amount_currency = False
                        vat_amount_currency = 0
                        percentage = (100/(1 + (self.advance_payment_vat.amount/100)) * (self.advance_payment_vat.amount/100))
                        amount_tax = (100/(1 + self.advance_payment_vat.amount)) * self.advance_payment_vat.amount /100
                        amount_untaxed = 100 - (100/(1 + self.advance_payment_vat.amount)) * self.advance_payment_vat.amount 
                        if 'amount_currency' in line:
                            line['amount_currency'], tmp_vat_amount_currency = self.decrease_tax_value(line['amount_currency'], percentage/100)
                        line[field_name], vat_amount = self.decrease_tax_value(line[field_name], percentage/100)
                        if 'amount_currency' in line and line['amount_currency'] != 0:
                            vat_amount = self.env['res.currency'].browse(line['currency_id'])._convert(tmp_vat_amount_currency, self.company_id.currency_id, self.company_id, fields.Date.today())
                        
                        if order_currency_id != company_currency:
                            if tmp_vat_amount_currency:
                                vat_amount_currency = tmp_vat_amount_currency
                            new_currency_id = order_currency_id
                
                
        if (self.advance_payment_vat or self.purchase_id or self.order_id) and vat_amount != 0:
            new_tax_line =  {
                    'name': 'VAT %s%%' %(round(((amount_tax*100)/amount_untaxed), 2)),
                    'amount_currency':0,
                    'debit': abs(vat_amount) if (self.purchase_id or (self.advance_payment_vat and self.payment_type == 'outbound')) else 0.0,
                    'currency_id': None,
                    'credit': abs(vat_amount) if (self.order_id or (self.advance_payment_vat and self.payment_type == 'inbound')) else 0.0,
                    'date_maturity': self.date,
                    'partner_id': self.partner_id.id,
                    'account_id': prepayment_tax_account.id if prepayment_tax_account else prepayment_account.id,
                    'payment_id': self.id,
                    'taxed_line': True,
                }
                
            all_move_vals.append(new_tax_line)

        return all_move_vals    
        
            
    def _synchronize_from_moves(self, changed_fields):
        if self.advance_payment:
            return super(AccountPayment, self.with_context(skip_account_move_synchronization=True))._synchronize_from_moves(changed_fields)
        else:
            return super()._synchronize_from_moves(changed_fields)
    def _prepare_move_line_default_vals111(self, write_off_line_vals=None):
        """
        Call super _prepare_payment_moves that returns list of journal entries containing dictionaries of journal items
        For each journal entry loop over the journal items.
        Check if payment journal is advanced payment and has tax.
        If yes then reduce by the tax and create a new journal item with tax
        """
        res = super()._prepare_move_line_default_vals(write_off_line_vals)
        pre_receive = self.partner_id.prepayment_receivable_id or (self.partner_id.parent_id.prepayment_receivable_id if self.partner_id.parent_id else False)
        pre_receive_vat = self.partner_id.prepayment_vat_receivable_id or (self.partner_id.parent_id.prepayment_vat_receivable_id if self.partner_id.parent_id else False)
        pre_payable = self.partner_id.prepayment_payable_id or (self.partner_id.parent_id.prepayment_payable_id if self.partner_id.parent_id else False)
        pre_payable_vat = self.partner_id.prepayment_vat_payable_id or (self.partner_id.parent_id.prepayment_vat_payable_id if self.partner_id.parent_id else False)
        if self.advance_payment:
            if (not pre_receive or not pre_receive_vat)  and self.payment_type == 'inbound':
                raise ValidationError(_('Configure Partner Pre-Payment accounts'))
            if (not pre_payable or not pre_payable_vat)  and self.payment_type == 'outbound':
                raise ValidationError(_('Configure Partner Pre-Payment accounts'))
        all_move_vals = super(AccountPayment, self)._prepare_move_line_default_vals()
        company_currency = self.company_id.currency_id
        for move_vals in all_move_vals:
            if self.advance_payment:
                if self.order_id:
                    account_id = self.partner_id.property_account_receivable_id.id
                    prepayment_account = pre_receive
                    amount_total = self.order_id.amount_total
                    amount_tax = self.order_id.amount_tax
                    prepayment_tax_account = pre_receive_vat if amount_tax > 0.0 else None
                    order_currency_id = self.order_id.pricelist_id.currency_id
                    field_name = 'credit'
                elif self.purchase_id:
                    account_id = self.partner_id.property_account_payable_id.id
                    prepayment_account = pre_payable
                    amount_total = self.purchase_id.amount_total
                    amount_tax = self.purchase_id.amount_tax
                    prepayment_tax_account = pre_payable_vat if amount_tax > 0.0 else None
                    order_currency_id = self.purchase_id.currency_id
                    field_name = 'debit'
                elif self.advance_payment:
                    order_currency_id = self.currency_id
                    prepayment_tax_account = pre_payable_vat if self.payment_type != 'inbound'  else pre_receive_vat
                    
                if self.purchase_id or self.order_id:
                    rate = self.manual_currency_exchange_rate if self.apply_manual_currency_exchange else order_currency_id.rate


                    if  order_currency_id != self.company_currency_id:
                        order_rate = rate if order_currency_id == self.currency_id else order_currency_id.rate
                        amount_total = amount_total / order_rate
                        amount_tax = amount_tax / order_rate
                
                vat_amount_currency = 0.0
                new_currency_id = None
                vat_amount = 0.0
                if self.purchase_id or self.order_id:
                    amount_untaxed = amount_total - amount_tax
                    
                for line in move_vals['line_ids']:
                    if line[2]['account_id'] == self.partner_id.property_account_receivable_id.id or line[2]['account_id'] == self.partner_id.property_account_payable_id.id:
                        if (self.payment_type =='inbound' and pre_receive.id ) or ( self.payment_type == 'outbound' and pre_payable.id):
                            line[2]['account_id'] = self.payment_type =='inbound' and pre_receive.id or pre_payable.id
                    if (self.purchase_id or self.order_id) and ((pre_receive and pre_receive.id ==  line[2]['account_id']) or  (pre_payable and line[2]['account_id'] == pre_payable.id)):

                        if line[2][field_name]:
                            tmp_vat_amount_currency = False
                            vat_amount_currency = 0
                            percentage = (amount_total - amount_untaxed) / amount_total
                            if 'amount_currency' in line[2]:
                                line[2]['amount_currency'], tmp_vat_amount_currency = self.decrease_tax_value(line[2]['amount_currency'], percentage)
                            line[2][field_name], vat_amount = self.decrease_tax_value(line[2][field_name], percentage)
                            if 'amount_currency' in line[2] and line[2]['amount_currency'] != 0:
                                vat_amount = self.env['res.currency'].browse(line[2]['currency_id'])._convert(tmp_vat_amount_currency, self.company_id.currency_id, self.company_id, fields.Date.today())
                            
                            if order_currency_id != company_currency:
                                if tmp_vat_amount_currency:
                                    vat_amount_currency = tmp_vat_amount_currency
                                new_currency_id = order_currency_id
                    if self.advance_payment_vat and ((pre_receive and pre_receive.id ==  line[2]['account_id']) or  (pre_payable and line[2]['account_id'] == pre_payable.id)):
                        field_name = self.payment_type == 'outbound' and 'debit' or 'credit'
                        
                        if line[2][field_name]:
                            tmp_vat_amount_currency = False
                            vat_amount_currency = 0
                            percentage = (100/(1 + (self.advance_payment_vat.amount/100)) * (self.advance_payment_vat.amount/100))
                            amount_tax = (100/(1 + self.advance_payment_vat.amount)) * self.advance_payment_vat.amount /100
                            amount_untaxed = 100 - (100/(1 + self.advance_payment_vat.amount)) * self.advance_payment_vat.amount 
                            if 'amount_currency' in line[2]:
                                line[2]['amount_currency'], tmp_vat_amount_currency = self.decrease_tax_value(line[2]['amount_currency'], percentage/100)
                            line[2][field_name], vat_amount = self.decrease_tax_value(line[2][field_name], percentage/100)
                            if 'amount_currency' in line[2] and line[2]['amount_currency'] != 0:
                                vat_amount = self.env['res.currency'].browse(line[2]['currency_id'])._convert(tmp_vat_amount_currency, self.company_id.currency_id, self.company_id, fields.Date.today())
                            
                            if order_currency_id != company_currency:
                                if tmp_vat_amount_currency:
                                    vat_amount_currency = tmp_vat_amount_currency
                                new_currency_id = order_currency_id
                
                
                if (self.advance_payment_vat or self.purchase_id or self.order_id) and move_vals['line_ids'] and vat_amount != 0:
                    new_tax_line =  {
                            'name': 'VAT %s%%' %(round(((amount_tax*100)/amount_untaxed), 2)),
                            'amount_currency':0,
                            'debit': abs(vat_amount) if (self.purchase_id or (self.advance_payment_vat and self.payment_type == 'outbound')) else 0.0,
                            'currency_id': None,
                            'credit': abs(vat_amount) if (self.order_id or (self.advance_payment_vat and self.payment_type == 'inbound')) else 0.0,
                            'date_maturity': self.date,
                            'partner_id': self.partner_id.id,
                            'account_id': prepayment_tax_account.id if prepayment_tax_account else prepayment_account.id,
                            'payment_id': self.id,
                            'taxed_line': True
                        }
                        
                    move_vals['line_ids'].append((0, 0, new_tax_line))
        return all_move_vals


