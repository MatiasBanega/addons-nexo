from odoo import fields, models

import logging

log = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'
    
    advance_payment_moves = fields.Many2many('account.move', 'move_advance_payment_move', 'move_id', 'advance_payment_move_id')
    reversed_advance_payment = fields.Many2one('account.move', 'Reversed Advance Payments')
    
    def _prepare_reversed_advance_moves(self):
        total_credit = 0.0
        total_debit = 0.0
        total_tax = 0.0
        amount_currency_tax = 0
        amount_currency = 0
        balance = 0
        
        payment_type = None
        if self._context.get('create_type',False):
            move = self
        else:
            move = self.advance_payment_moves
        
        for line in move.mapped('line_ids'):
            payment_type = line.payment_id.payment_type
            if line.taxed_line:
                total_tax += line.credit if payment_type == 'inbound' else line.debit
                amount_currency_tax += line.amount_currency
                
            if (line.account_id == line.move_id.partner_id.prepayment_receivable_id or line.account_id == line.move_id.partner_id.prepayment_payable_id):
                balance += line.balance
                amount_currency += line.amount_currency
            
        if self.move_type == 'out_invoice' or self._context.get('create_type','non') == 'out_invoice':
            pre_account = self.partner_id.prepayment_receivable_id or (self.partner_id.parent_id.prepayment_receivable_id if self.partner_id.parent_id else False)
            pre_account_vat = self.partner_id.prepayment_vat_receivable_id or (self.partner_id.parent_id.prepayment_vat_receivable_id if self.partner_id.parent_id else False)
            reversal_rec_pay_account = self.partner_id.property_account_receivable_id
        else:
            pre_account = self.partner_id.prepayment_payable_id or (self.partner_id.parent_id.prepayment_payable_id if self.partner_id.parent_id else False)
            pre_account_vat = self.partner_id.prepayment_vat_payable_id or (self.partner_id.parent_id.prepayment_vat_payable_id if self.partner_id.parent_id else False)
            reversal_rec_pay_account = self.partner_id.property_account_payable_id
        lines = [(0, 0, {'name': 'Reverse Advance Payment',
                        'debit': -balance if balance<0 else 0,
                        'credit': balance if balance >0 else 0,
                        'currency_id' : self.currency_id.id if self.currency_id != self.company_id.currency_id else False,
                        'amount_currency' : -abs(amount_currency) if balance>0 else abs(amount_currency),
                        'date_maturity': self.date,
                        'partner_id': self.partner_id.id,
                        'account_id': pre_account.id,
                        'payment_id': None
                }), (0, 0, {'name': 'Reverse Advance Payment',
                            'debit': (balance + abs(total_tax)) if balance >0 else 0,
                            'credit': (-balance +total_tax)  if balance<0 else 0,
                            'currency_id' : self.currency_id.id if self.currency_id != self.company_id.currency_id else False,
                            'amount_currency' : -(abs(amount_currency) + abs(amount_currency_tax)) if balance<0 else (abs(amount_currency) + abs(amount_currency_tax)),
                            'date_maturity': self.date,
                            'partner_id': self.partner_id.id,
                            'account_id': reversal_rec_pay_account.id,
                            'payment_id': None
                })]
        if total_tax > 0.0:
            lines.append((0, 0, {'name': 'Reversed Tax %s %%' %(round(total_tax, 2)),
                                'debit': total_tax if payment_type == 'inbound' else 0.0,
                                'amount_currency': (abs(amount_currency_tax)) if payment_type == 'inbound' else -(abs(amount_currency_tax) ),
                                'credit': total_tax if payment_type == 'outbound' else 0.0,
                                'date_maturity': self.date,
                                'currency_id' : self.currency_id.id if self.currency_id != self.company_id.currency_id else False,
                                'partner_id': self.partner_id.id,
                                'account_id': pre_account_vat.id,
                                'payment_id': None,
                                'taxed_line': True
                            }))
    
        return lines
        
    def write(self, vals):
        res = super().write(vals)
        
        for record in self:
            if 'state' in vals and not self.env.context.get('skip_write'):
                if record.state == 'posted' and record.advance_payment_moves:
                    
                    if not record.reversed_advance_payment:
                        advance_payment = self.env['account.move'].create({'move_type': 'entry','date':record.date})
                        record.reversed_advance_payment = advance_payment
                        record.reversed_advance_payment.write({'line_ids': record._prepare_reversed_advance_moves()})
                        record.reversed_advance_payment.with_context(skip_write=True).action_post()

                    else:
                        lines = record._prepare_reversed_advance_moves()
                        record.reversed_advance_payment.write({"line_ids": [(2, line.id) for line in record.reversed_advance_payment.line_ids]})
                        record.reversed_advance_payment.write({'line_ids': record._prepare_reversed_advance_moves()})
                        record.reversed_advance_payment.with_context(skip_write=True).action_post()
                
                if record.state == 'draft' and record.reversed_advance_payment:
                    record.reversed_advance_payment.button_draft()
                    
        return res
    
class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    
    taxed_line = fields.Boolean('Taxed Line')