# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    internal_transfer_type = fields.Selection([
        ('j_to_j', 'Journal To Journal'), ('j_to_a', 'Direct Pay')], string=' Internal Transfer Type', default='')
    from_account_id = fields.Many2one('account.account', string="From Account")
    to_account_id = fields.Many2one('account.account', string="To Account")

    @api.onchange('destination_journal_id')
    def on_change_destination_journal_id(self):
        if self.destination_account_id and self.internal_transfer_type == 'j_to_j':
            self.partner_id = self.env.user.company_id.partner_id.id

    @api.depends('is_internal_transfer')
    def _compute_partner_id(self):
        for pay in self:
            if pay.is_internal_transfer and pay.internal_transfer_type == 'j_to_j':
                super(AccountPayment, pay)._compute_partner_id()
            else:
                pass

    @api.depends('journal_id', 'destination_journal_id')
    def _compute_is_internal_transfer(self):
        for payment in self:
            if payment.is_internal_transfer and payment.internal_transfer_type == 'j_to_j':
                super(AccountPayment, payment)._compute_is_internal_transfer()
            else:
                if self._context.get('dont_redirect_to_payments'):
                    payment.is_internal_transfer = False
                else:
                    is_partner_ok = payment.partner_id
                    is_account_ok = payment.destination_account_id or payment.journal_id.company_id.transfer_account_id
                    payment.is_internal_transfer = is_partner_ok and is_account_ok
                if not payment.internal_transfer_type:
                    payment.is_internal_transfer = False

    @api.depends('journal_id', 'payment_type', 'payment_method_line_id', 'internal_transfer_type', 'from_account_id')
    def _compute_outstanding_account_id(self):
        for pay in self:
            if pay.internal_transfer_type in ('a_to_a', 'j_to_a', 'a_to_j') and pay.is_internal_transfer:
                if pay.internal_transfer_type == 'a_to_a':
                    pay.outstanding_account_id = pay.from_account_id.id

                if pay.internal_transfer_type == 'a_to_j':
                    pay.outstanding_account_id = pay.from_account_id.id

                if pay.internal_transfer_type == 'j_to_a':
                    pay.outstanding_account_id = pay.journal_id.default_account_id.id
            else:
                if pay.payment_type == 'inbound':
                    pay.outstanding_account_id = (pay.payment_method_line_id.payment_account_id
                                                  or pay.journal_id.company_id.account_journal_payment_debit_account_id)
                elif pay.payment_type == 'outbound':
                    pay.outstanding_account_id = (pay.payment_method_line_id.payment_account_id
                                                  or pay.journal_id.company_id.account_journal_payment_credit_account_id)
                else:
                    pay.outstanding_account_id = False

    @api.depends('journal_id', 'partner_id', 'partner_type', 'is_internal_transfer', 'internal_transfer_type',
                 'to_account_id')
    def _compute_destination_account_id(self):
        self.destination_account_id = False
        for pay in self:
            if pay.internal_transfer_type in ('a_to_a', 'j_to_a', 'a_to_j') and pay.is_internal_transfer:
                if pay.is_internal_transfer:
                    pay.destination_account_id = pay.journal_id.company_id.transfer_account_id
                    # Custom Code
                    if pay.internal_transfer_type == 'a_to_a':
                        pay.destination_account_id = pay.to_account_id

                    if pay.internal_transfer_type == 'a_to_j':
                        pay.destination_account_id = pay.destination_journal_id.default_account_id

                    if pay.internal_transfer_type == 'j_to_a':
                        pay.destination_account_id = pay.to_account_id

                elif pay.partner_type == 'customer':
                    # Receive money from invoice or send money to refund it.
                    if pay.partner_id:
                        pay.destination_account_id = pay.partner_id.with_company(
                            pay.company_id).property_account_receivable_id
                    else:
                        pay.destination_account_id = self.env['account.account'].search([
                            ('company_id', '=', pay.company_id.id),
                            ('internal_type', '=', 'receivable'),
                            ('deprecated', '=', False),
                        ], limit=1)
                elif pay.partner_type == 'supplier':
                    # Send money to pay a bill or receive money to refund it.
                    if pay.partner_id:
                        pay.destination_account_id = pay.partner_id.with_company(
                            pay.company_id).property_account_payable_id
                    else:
                        pay.destination_account_id = self.env['account.account'].search([
                            ('company_id', '=', pay.company_id.id),
                            ('internal_type', '=', 'payable'),
                            ('deprecated', '=', False),
                        ], limit=1)
            else:
                if pay.is_internal_transfer:
                    pay.destination_account_id = pay.journal_id.company_id.transfer_account_id
                elif pay.partner_type == 'customer':
                    # Receive money from invoice or send money to refund it.
                    if pay.partner_id:
                        pay.destination_account_id = pay.partner_id.with_company(
                            pay.company_id).property_account_receivable_id
                    else:
                        pay.destination_account_id = self.env['account.account'].search([
                            ('company_id', '=', pay.company_id.id),
                            ('internal_type', '=', 'receivable'),
                            ('deprecated', '=', False),
                        ], limit=1)
                elif pay.partner_type == 'supplier':
                    # Send money to pay a bill or receive money to refund it.
                    if pay.partner_id:
                        pay.destination_account_id = pay.partner_id.with_company(
                            pay.company_id).property_account_payable_id
                    else:
                        pay.destination_account_id = self.env['account.account'].search([
                            ('company_id', '=', pay.company_id.id),
                            ('internal_type', '=', 'payable'),
                            ('deprecated', '=', False),
                        ], limit=1)

    # def _prepare_move_line_default_vals(self, write_off_line_vals=None):
    #     if self.is_internal_transfer and self.internal_transfer_type == 'j_to_j':
    #         return super(AccountPayment, self)._prepare_move_line_default_vals()
    #     self.ensure_one()
    #     write_off_line_vals = write_off_line_vals or {}
    #
    #     if not self.outstanding_account_id:
    #         raise UserError(_(
    #             "You can't create a new payment without an outstanding payments/receipts account set either on the "
    #             "company or the %s payment method in the %s journal.",
    #             self.payment_method_line_id.name, self.journal_id.display_name))
    #
    #     # Compute amounts.
    #     write_off_amount_currency = write_off_line_vals.get('amount', 0.0)
    #
    #     if self.payment_type == 'inbound':
    #         # Receive money.
    #         liquidity_amount_currency = self.amount
    #     elif self.payment_type == 'outbound':
    #         # Send money.
    #         liquidity_amount_currency = -self.amount
    #         write_off_amount_currency *= -1
    #     else:
    #         liquidity_amount_currency = write_off_amount_currency = 0.0
    #
    #     write_off_balance = self.currency_id._convert(
    #         write_off_amount_currency,
    #         self.company_id.currency_id,
    #         self.company_id,
    #         self.date,
    #     )
    #     liquidity_balance = self.currency_id._convert(
    #         liquidity_amount_currency,
    #         self.company_id.currency_id,
    #         self.company_id,
    #         self.date,
    #     )
    #     counterpart_amount_currency = -liquidity_amount_currency - write_off_amount_currency
    #     counterpart_balance = -liquidity_balance - write_off_balance
    #     currency_id = self.currency_id.id
    #
    #     if self.is_internal_transfer:
    #         if self.payment_type == 'inbound':
    #             liquidity_line_name = _('Transfer to %s', self.journal_id.name)
    #         else:  # payment.payment_type == 'outbound':
    #             liquidity_line_name = _('Transfer from %s', self.journal_id.name)
    #     else:
    #         liquidity_line_name = self.payment_reference
    #
    #     # Compute a default label to set on the journal items.
    #
    #     payment_display_name = {
    #         'outbound-customer': _("Customer Reimbursement"),
    #         'inbound-customer': _("Customer Payment"),
    #         'outbound-supplier': _("Vendor Payment"),
    #         'inbound-supplier': _("Vendor Reimbursement"),
    #     }
    #
    #     default_line_name = self.env['account.move.line']._get_default_line_name(
    #         _('Internal Transfer') if self.is_internal_transfer else payment_display_name[
    #             '%s-%s' % (self.payment_type, self.partner_type)], self.amount, self.currency_id, self.date,
    #         partner=self.partner_id)
    #
    #     liquidity_line_account = self.journal_id.company_id.account_journal_payment_credit_account_id.id if liquidity_balance < 0.0 else self.journal_id.company_id.account_journal_payment_debit_account_id.id
    #     # Custom Code
    #     if self.is_internal_transfer and self.internal_transfer_type == 'a_to_a':
    #         liquidity_line_account = self.from_account_id.id
    #
    #     if self.is_internal_transfer == True and self.internal_transfer_type == 'a_to_j':
    #         liquidity_line_account = self.from_account_id.id
    #
    #     if self.is_internal_transfer == True and self.internal_transfer_type == 'j_to_a':
    #         liquidity_line_account = self.from_journal_id.default_account_id.id
    #
    #     if self.is_internal_transfer == True and self.internal_transfer_type == 'j_to_j':
    #         liquidity_line_account = self.from_journal_id.default_account_id.id
    #     line_vals_list = [
    #         # Liquidity line.
    #         {
    #             'name': liquidity_line_name or default_line_name,
    #             'date_maturity': self.date,
    #             'amount_currency': liquidity_amount_currency,
    #             'currency_id': currency_id,
    #             'debit': liquidity_balance if liquidity_balance > 0.0 else 0.0,
    #             'credit': -liquidity_balance if liquidity_balance < 0.0 else 0.0,
    #             'partner_id': self.partner_id.id,
    #             'account_id': liquidity_line_account,
    #         },
    #         # Receivable / Payable.
    #         {
    #             'name': self.payment_reference or default_line_name,
    #             'date_maturity': self.date,
    #             'amount_currency': counterpart_amount_currency,
    #             'currency_id': currency_id,
    #             'debit': counterpart_balance if counterpart_balance > 0.0 else 0.0,
    #             'credit': -counterpart_balance if counterpart_balance < 0.0 else 0.0,
    #             'partner_id': self.partner_id.id,
    #             'account_id': self.destination_account_id.id,
    #         },
    #     ]
    #     if not self.currency_id.is_zero(write_off_amount_currency):
    #         # Write-off line.
    #         line_vals_list.append({
    #             'name': write_off_line_vals.get('name') or default_line_name,
    #             'amount_currency': write_off_amount_currency,
    #             'currency_id': currency_id,
    #             'debit': write_off_balance if write_off_balance > 0.0 else 0.0,
    #             'credit': -write_off_balance if write_off_balance < 0.0 else 0.0,
    #             'partner_id': self.partner_id.id,
    #             'account_id': write_off_line_vals.get('account_id'),
    #         })
    #     return line_vals_list

    def _synchronize_to_moves(self, changed_fields):
        ''' Update the account.move regarding the modified account.payment.
        :param changed_fields: A list containing all modified fields on account.payment.
        '''
        if self and not self[0].is_internal_transfer:
            return super(AccountPayment, self)._synchronize_to_moves(changed_fields)
        if self.is_internal_transfer and self.internal_transfer_type == 'j_to_j':
            if self._context.get('skip_account_move_synchronization'):
                return

            if not any(field_name in changed_fields for field_name in (
                'date', 'amount', 'payment_type', 'partner_type', 'payment_reference', 'is_internal_transfer',
                'currency_id', 'partner_id', 'destination_account_id', 'partner_bank_id', 'to_account_id', 'from_account_id',
                'internal_transfer_type', 'destination_journal_id'
            )):
                return

            for pay in self.with_context(skip_account_move_synchronization=True):
                liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()

                # Make sure to preserve the write-off amount.
                # This allows to create a new payment with custom 'line_ids'.

                if writeoff_lines:
                    counterpart_amount = sum(counterpart_lines.mapped('amount_currency'))
                    writeoff_amount = sum(writeoff_lines.mapped('amount_currency'))

                    # To be consistent with the payment_difference made in account.payment.register,
                    # 'writeoff_amount' needs to be signed regarding the 'amount' field before the write.
                    # Since the write is already done at this point, we need to base the computation on accounting values.
                    if (counterpart_amount > 0.0) == (writeoff_amount > 0.0):
                        sign = -1
                    else:
                        sign = 1
                    writeoff_amount = abs(writeoff_amount) * sign

                    write_off_line_vals = {
                        'name': writeoff_lines[0].name,
                        'amount': writeoff_amount,
                        'account_id': writeoff_lines[0].account_id.id,
                    }
                else:
                    write_off_line_vals = {}

                line_vals_list = pay._prepare_move_line_default_vals(write_off_line_vals=write_off_line_vals)

                line_ids_commands = [
                    (1, liquidity_lines.id, line_vals_list[0]),
                    (1, counterpart_lines.id, line_vals_list[1]),
                ]

                for line in writeoff_lines:
                    line_ids_commands.append((2, line.id))

                for extra_line_vals in line_vals_list[2:]:
                    line_ids_commands.append((0, 0, extra_line_vals))

                # Update the existing journal items.
                # If dealing with multiple write-off lines, they are dropped and a new one is generated.

                pay.move_id.write({
                    'partner_id': pay.partner_id.id,
                    'currency_id': pay.currency_id.id,
                    'partner_bank_id': pay.partner_bank_id.id,
                    'line_ids': line_ids_commands,
                })
        else:
            if self._context.get('skip_account_move_synchronization'):
                return

            if not any(field_name in changed_fields for field_name in (
                'date', 'amount', 'payment_type', 'partner_type', 'payment_reference', 'is_internal_transfer',
                'currency_id', 'partner_id', 'destination_account_id', 'partner_bank_id', 'to_account_id', 'from_account_id',
                'internal_transfer_type', 'destination_journal_id'
            )):
                return

            for pay in self.with_context(skip_account_move_synchronization=True):
                liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()

                # Make sure to preserve the write-off amount.
                # This allows to create a new payment with custom 'line_ids'.

                if writeoff_lines:
                    counterpart_amount = sum(counterpart_lines.mapped('amount_currency'))
                    writeoff_amount = sum(writeoff_lines.mapped('amount_currency'))

                    # To be consistent with the payment_difference made in account.payment.register,
                    # 'writeoff_amount' needs to be signed regarding the 'amount' field before the write.
                    # Since the write is already done at this point, we need to base the computation on accounting values.
                    if (counterpart_amount > 0.0) == (writeoff_amount > 0.0):
                        sign = -1
                    else:
                        sign = 1
                    writeoff_amount = abs(writeoff_amount) * sign

                    write_off_line_vals = {
                        'name': writeoff_lines[0].name,
                        'amount': writeoff_amount,
                        'account_id': writeoff_lines[0].account_id.id,
                    }
                else:
                    write_off_line_vals = {}

                line_vals_list = pay._prepare_move_line_default_vals(write_off_line_vals=write_off_line_vals)
                lines = liquidity_lines + counterpart_lines
                line_ids_commands = [
                    (1, lines[0].id, line_vals_list[0]),
                    (1, lines[1].id, line_vals_list[1]),
                ]

                for line in writeoff_lines:
                    line_ids_commands.append((2, line.id))

                for extra_line_vals in line_vals_list[2:]:
                    line_ids_commands.append((0, 0, extra_line_vals))

                # Update the existing journal items.
                # If dealing with multiple write-off lines, they are dropped and a new one is generated.

                pay.move_id.write({
                    'partner_id': pay.partner_id.id,
                    'currency_id': pay.currency_id.id,
                    'partner_bank_id': pay.partner_bank_id.id,
                    'line_ids': line_ids_commands,
                })

    def _synchronize_from_moves(self, changed_fields):
        ''' Update the account.payment regarding its related account.move.
        Also, check both models are still consistent.
        :param changed_fields: A set containing all modified fields on account.move.
        '''
        if self and not self[0].is_internal_transfer:
            return super(AccountPayment, self)._synchronize_from_moves(changed_fields)
        else:
            if self._context.get('skip_account_move_synchronization'):
                return

            for pay in self.with_context(skip_account_move_synchronization=True):

                # After the migration to 14.0, the journal entry could be shared between the account.payment and the
                # account.bank.statement.line. In that case, the synchronization will only be made with the statement line.
                if pay.move_id.statement_line_id:
                    continue

                move = pay.move_id
                move_vals_to_write = {}
                payment_vals_to_write = {}

                if 'journal_id' in changed_fields:
                    if pay.journal_id.type not in ('bank', 'cash'):
                        raise UserError(_("A payment must always belongs to a bank or cash journal."))

                if 'line_ids' in changed_fields:
                    all_lines = move.line_ids
                    liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()
                    lines = liquidity_lines + counterpart_lines
                    liquidity_lines = lines[0]
                    counterpart_lines = lines[1]

                    if len(liquidity_lines) != 1:
                        raise UserError(_(
                            "Journal Entry %s is not valid. In order to proceed, the journal items must "
                            "include one and only one outstanding payments/receipts account.",
                            move.display_name,
                        ))

                    if len(counterpart_lines) != 1:
                        raise UserError(_(
                            "Journal Entry %s is not valid. In order to proceed, the journal items must "
                            "include one and only one receivable/payable account (with an exception of "
                            "internal transfers).",
                            move.display_name,
                        ))

                    if writeoff_lines and len(writeoff_lines.account_id) != 1:
                        raise UserError(_(
                            "Journal Entry %s is not valid. In order to proceed, "
                            "all optional journal items must share the same account.",
                            move.display_name,
                        ))

                    if any(line.currency_id != all_lines[0].currency_id for line in all_lines):
                        raise UserError(_(
                            "Journal Entry %s is not valid. In order to proceed, the journal items must "
                            "share the same currency.",
                            move.display_name,
                        ))

                    if any(line.partner_id != all_lines[0].partner_id for line in all_lines):
                        raise UserError(_(
                            "Journal Entry %s is not valid. In order to proceed, the journal items must "
                            "share the same partner.",
                            move.display_name,
                        ))

                    # if counterpart_lines.account_id.user_type_id.type == 'receivable':
                    #     partner_type = 'customer'
                    # else:
                    #     partner_type = 'supplier'

                    liquidity_amount = liquidity_lines.amount_currency

                    move_vals_to_write.update({
                        'currency_id': liquidity_lines.currency_id.id,
                        'partner_id': liquidity_lines.partner_id.id,
                    })
                    payment_vals_to_write.update({
                        'amount': abs(liquidity_amount),
                        'partner_type': pay.partner_type,
                        'currency_id': liquidity_lines.currency_id.id,
                        'destination_account_id': counterpart_lines.account_id.id,
                        'partner_id': liquidity_lines.partner_id.id,
                    })
                    if liquidity_amount > 0.0:
                        payment_vals_to_write.update({'payment_type': 'inbound'})
                    elif liquidity_amount < 0.0:
                        payment_vals_to_write.update({'payment_type': 'outbound'})

                move.write(move._cleanup_write_orm_values(move, move_vals_to_write))
                pay.write(move._cleanup_write_orm_values(pay, payment_vals_to_write))

    def _seek_for_lines(self):
        """ Helper used to dispatch the journal items between:
        - The lines using the temporary liquidity account.
        - The lines using the counterpart account.
        - The lines being the write-off lines.
        :return: (liquidity_lines, counterpart_lines, writeoff_lines)
        """
        if self and not self[0].is_internal_transfer:
            return super(AccountPayment, self)._seek_for_lines()
        if self.is_internal_transfer and self.internal_transfer_type == 'j_to_j':
            return super(AccountPayment, self)._seek_for_lines()
        self.ensure_one()

        liquidity_lines = self.env['account.move.line']
        counterpart_lines = self.env['account.move.line']
        writeoff_lines = self.env['account.move.line']
        for line in self.move_id.line_ids:
            if self.is_internal_transfer == True and self.internal_transfer_type in ['a_to_a', 'a_to_j']:
                if line.account_id in (
                        self.from_account_id,
                        self.payment_method_line_id.payment_account_id,
                        self.journal_id.company_id.account_journal_payment_debit_account_id,
                        self.journal_id.company_id.account_journal_payment_credit_account_id,
                        self.journal_id.inbound_payment_method_line_ids.payment_account_id,
                        self.journal_id.outbound_payment_method_line_ids.payment_account_id,
                ):
                    liquidity_lines += line
                elif line.account_id.internal_type in ('receivable', 'payable', 'liquidity', 'other'):
                    counterpart_lines += line
                else:
                    writeoff_lines += line
            elif self.is_internal_transfer == True and self.internal_transfer_type in ['j_to_a', 'j_to_j']:
                if line.account_id in (
                        self.journal_id.default_account_id,
                        self.payment_method_line_id.payment_account_id,
                        self.journal_id.company_id.account_journal_payment_debit_account_id,
                        self.journal_id.company_id.account_journal_payment_credit_account_id,
                        self.journal_id.inbound_payment_method_line_ids.payment_account_id,
                        self.journal_id.outbound_payment_method_line_ids.payment_account_id,
                ):
                    liquidity_lines += line
                elif line.account_id.internal_type in ('receivable', 'payable', 'liquidity', 'other'):
                    counterpart_lines += line
                else:
                    writeoff_lines += line
            else:
                if line.account_id in self._get_valid_liquidity_accounts():
                    liquidity_lines += line
                elif line.account_id.internal_type in (
                        'receivable', 'payable') or line.partner_id == line.company_id.partner_id:
                    counterpart_lines += line
                else:
                    writeoff_lines += line
        return liquidity_lines, counterpart_lines, writeoff_lines

    def action_post(self):
        ''' draft -> posted '''
        self.move_id._post(soft=False)

        self.filtered(
            lambda pay: pay.is_internal_transfer and pay.internal_transfer_type == 'j_to_j' and not pay.paired_internal_transfer_payment_id
        )._create_paired_internal_transfer_payment()
