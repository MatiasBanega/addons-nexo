from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)


class ProductTempExt(models.Model):
    _inherit = 'product.template'

    is_sweep_product = fields.Boolean(string="Is a Sweep Product")
    sweep_account_id = fields.Many2one('account.account')


class ResCompanyExt(models.Model):
    _inherit = 'res.company'

    sweep_start_date = fields.Date('Start Date')
    sweep_end_date = fields.Date('End Date')


class AccountMoveExt(models.Model):
    _inherit = 'account.move'

    is_a_sweep_je = fields.Boolean()
    ref_line_id = fields.Many2one('account.move.line', "Reference Line")
    # analytic_account_id = fields.Many2one(string='Project')

    # vendor_bill_line_id = fields.Many2one('account.move.line', "Vendor Bill Line")

    # def button_cancel(self):
    #     logging.info("Hamza Ilyas ----> button_cancel Called")
    #     for move in self:
    #         if not move.journal_id.update_posted:
    #             raise UserError(
    #                 _('You cannot modify a posted entry of this journal.\nFirst you should set the journal to allow cancelling entries.'))
    #         else:
    #             if move.is_a_sweep_je:
    #                 if move.ref:
    #                     bill = self.env['account.move'].search([('number', '=', move.ref)])
    #                     if bill:
    #                         self.unswept_bill_lines(move)
    #                     else:
    #                         # receipt = self.env['account.voucher'].search([('number', '=', move.ref)])
    #                         # if receipt:
    #                         #     self.unswept_voucher_lines(move)
    #                         # else:
    #                             expense = self.env['hr.expense'].search([('name', '=', move.ref)])
    #                             if expense:
    #                                 self.unswept_expense(expense)
    #                 # for line in move.line_ids:
    #                 #     line.swept = False
    #
    #     if self.ids:
    #         self.check_access_rights('write')
    #         self.check_access_rule('write')
    #         self._check_lock_date()
    #         self._cr.execute('UPDATE account_move ' \
    #                          'SET state=%s ' \
    #                          'WHERE id IN %s', ('draft', tuple(self.ids),))
    #         self.invalidate_cache()
    #     self._check_lock_date()
    #
    #     # on cancelling of sweep journal entry it will be removed
    #     if self.is_a_sweep_je:
    #         logging.info("Hamza Ilyas ----> unlinking swept journal entry")
    #         self.unlink()
    #     return True

    def button_cancel(self):
        logging.info("Hamza Ilyas ----> button_cancel Called")
        self.write({'auto_post': False, 'state': 'cancel'})
        if self.is_a_sweep_je:
            if self.ref:
                print(self.ref)
                # move = self.env['account.move'].search([('name', '=', self.ref)])
                if self.ref_line_id:
                    self.unswept_move_lines()
                else:
                    expense = self.env['hr.expense'].search([('name', '=', self.ref)])
                    if expense:
                        self.unswept_expense(expense)
            logging.info("Hamza Ilyas ----> unlinking swept journal entry")
            action = self.env.ref('account.action_move_journal_line').read()[0]
            self.unlink()
            return action
            # return {'type': 'ir.actions.act_window_close'}
            # return {
            #     'context': self.env.context,
            #     'view_type': 'tree',
            #     'view_mode': 'tree',
            #     'res_model': 'account.move',
            #     # 'res_id': self.id,
            #     'view_id': self.env.ref('account.view_move_tree').id,
            #     'type': 'ir.actions.act_window',
            #     'target': 'new',
            # }

    def unswept_move_lines(self):
        # for line in bill.invoice_line_ids:
        #     for move_line in move.line_ids:
        #         if move_line.product_id.name == line.name and move_line.analytical_account_id == line.account_analytic_id:
        print("<<<<<<<<<<<unswept_move_lines called XXXXXXXX>>>>>>>>>>>")
        # line = False
        # if move.ref_line_id:
        print("ref_line_id")
        line = self.ref_line_id
        # if move.voucher_line_id:
        #     print("voucher_line_id")
        #     line = move.voucher_line_id
        print(line)
        if line:
            line.swept = False
            # line.move_id.swept = False
            line.invoice_line_id.swept = False
        print(line.swept)
        # print(line.move_id.swept)
        print(line.invoice_line_id.swept)

    # def unswept_voucher_lines(self, move):
    #     # for line in recipt.line_ids:
    #     #     for move_line in move.line_ids:
    #     #         if move_line.name == line.name and move_line.analytical_account_id == line.account_analytic_id:
    #     line = move.voucher_line_id
    #     line.swept = False
    #     line.invoice_line_id.swept = False
    #     line.voucher_id.swept = False

    def unswept_expense(self, expense):
        expense.swept = False
        if expense.invoice_line_id:
            expense.invoice_line_id.swept = False

    def cron_sweep_entries(self):
        logging.info("Hamza Ilyas ----> cron_sweep_entries called")
        start_date = self.env.company.sweep_start_date
        end_date = self.env.company.sweep_end_date
        invoices = self.env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), '&',
                                                    ('invoice_date', '>=', start_date),
                                                    ('invoice_date', '<=', end_date)])
        for invoice in invoices.filtered(lambda inv: inv.invoice_line_ids is not False):
            logging.info("Hamza Ilyas ----> <<<<<<<<<<INVOICE>>>>>>>>>>")
            # if invoice.invoice_line_ids:
            logging.info("Hamza Ilyas ----> <<<<<<<<<< Invoice is open or paid and have lines >>>>>>>>>>")
            for invoice_line in invoice.invoice_line_ids.filtered(lambda line: line.swept is False):
                # if not invoice_line.swept:
                logging.info("Hamza Ilyas ----> <<<<<<<<<< Invoice line is not swept >>>>>>>>>>")
                expense = self.check_ili_in_expenses(invoice_line, start_date, end_date)
                if expense:
                    self.swept_journal_entry(expense, end_date)
                    invoice_line.swept = True
                    continue

                purchase_receipt_line = self.check_ili_in_purchase_receipts(invoice_line, start_date, end_date)
                if purchase_receipt_line:
                    self.swept_journal_entry(purchase_receipt_line, end_date)
                    invoice_line.swept = True
                    continue

                sale_receipt_line = self.check_ili_in_sale_receipts(invoice_line, start_date, end_date)
                if sale_receipt_line:
                    self.swept_journal_entry(sale_receipt_line, end_date)
                    invoice_line.swept = True
                    continue

                bill_line = self.check_ili_in_vendor_bills(invoice_line, start_date, end_date)
                if bill_line:
                    self.swept_journal_entry(bill_line, end_date)
                    invoice_line.swept = True
                    continue

    def swept_journal_entry(self, record, end_date):
        logging.info("Hamza Ilyas ----> swept_journal_entry Called")
        journal = self.env['sweep.journal'].search([])
        sweep_journal = False
        if journal:
            sweep_journal = journal.journal_id
        else:
            raise ValidationError("Sweep Journal is not set")
        if record._name == 'hr.expense':
            logging.info("Hamza Ilyas ----> Expense Model")
            self.create_swept_journal_entry(record.name, False, sweep_journal, record.total_amount, record.product_id,
                                            record.analytic_account_id, record.partner_id, end_date)
        elif record._name == 'account.move.line':
            logging.info("Hamza Ilyas ----> -->")
            logging.info(record.move_id.move_type)
            # if record.move_id.move_type == 'in_invoice':
            self.create_swept_journal_entry(record.move_id.name, record, sweep_journal, record.price_unit,
                                            record.product_id, record.analytic_account_id, record.partner_id, end_date)
            # if record.move_id.move_type in ['in_receipt', 'out_receipt']:
            #     logging.info("Hamza Ilyas ----> Receipt Line Model")
            #     self.create_swept_journal_entry(record.move_id.name, False, record, sweep_journal, record.price_unit,
            #                                     record.product_id, record.analytic_account_id)

        # elif record._name == 'account.voucher.line':
        #     logging.info("Hamza Ilyas ----> Purchase Receipt Line Model")
        #     self.create_swept_journal_entry(record.voucher_id.number, False, record, sweep_journal, record.price_unit,
        #                                     record.product_id, record.account_analytic_id)

    def create_swept_journal_entry(self, je_ref, ref_line_id, je_journal, ji_amount, ji_product, analytic_account_id, partner, end_date):
        logging.info("Hamza Ilyas ----> create_swept_journal_entry Called")
        logging.info("Hamza Ilyas ----> <<<<<<<<<ji_amount>>>>>>>>>")
        logging.info(ji_amount)
        a_a_project = self.env['account.analytic.account'].search([('id', '=', analytic_account_id.id)])
        if a_a_project:
            logging.info("<<<<<<<<<<<<<<a_a_project>>>>>>>>>>>>>>")
            logging.info(a_a_project)
            analytic_account_id = a_a_project.id
        else:
            analytic_account_id = False
        self.env.cr.commit()
        if ji_product.property_account_expense_id:
            # create move
            # if vendor_bill_line:
            #     vendor_bill_line = vendor_bill_line.id
            # if voucher_line:
            #     voucher_line = voucher_line.id
            print("<<<<<<end_date>>>>>>")
            print(end_date)
            move = self.env['account.move'].create({'ref': je_ref, 'journal_id': je_journal.id, 'state': 'draft',
                                                    'is_a_sweep_je': True, 'ref_line_id': ref_line_id, 'date': end_date,
                                                    })

            # hi_date = datetime.combine(end_date, datetime.min.time())
            self.env.cr.execute("UPDATE ACCOUNT_MOVE SET DATE = '%s' WHERE id=%s" % (end_date, move.id))

            if move.ref_line_id:
                if move.ref_line_id.move_id.move_type == 'out_receipt':
                    move.write({'line_ids': [
                        (0, 0, {'account_id': ji_product.property_account_expense_id.id,
                                'name': ji_product.name,
                                'partner_id': partner.id,
                                'debit': 0.0,
                                'credit': ji_amount,
                                'move_id': move.id,
                                'project_id_hi': analytic_account_id,
                                'swept': True,
                                }),
                        (0, 0, {'account_id': ji_product.sweep_account_id.id,
                                'name': ji_product.name,
                                'partner_id': partner.id,
                                'debit': ji_amount,
                                'credit': 0.0,
                                'move_id': move.id,
                                'project_id_hi': analytic_account_id,
                                'swept': True,
                                }),
                    ], })
                else:
                    move.write({'line_ids': [
                        (0, 0, {'account_id': ji_product.property_account_expense_id.id,
                                'name': ji_product.name,
                                'partner_id': partner.id,
                                'debit': ji_amount,
                                'credit': 0.0,
                                'move_id': move.id,
                                'project_id_hi': analytic_account_id,
                                'swept': True,
                                }),
                        (0, 0, {'account_id': ji_product.sweep_account_id.id,
                                'name': ji_product.name,
                                'partner_id': partner.id,
                                'debit': 0.0,
                                'credit': ji_amount,
                                'move_id': move.id,
                                'project_id_hi': analytic_account_id,
                                'swept': True,
                                }),
                    ], })
            else:
                move.write({'line_ids': [
                    (0, 0, {'account_id': ji_product.property_account_expense_id.id,
                            'name': ji_product.name,
                            'partner_id': partner.id,
                            'debit': ji_amount,
                            'credit': 0.0,
                            'move_id': move.id,
                            'project_id_hi': analytic_account_id,
                            'swept': True,
                            }),
                    (0, 0, {'account_id': ji_product.sweep_account_id.id,
                            'name': ji_product.name,
                            'partner_id': partner.id,
                            'debit': 0.0,
                            'credit': ji_amount,
                            'move_id': move.id,
                            'project_id_hi': analytic_account_id,
                            'swept': True,
                            }),
                ], })
            if move:
                move.action_post()
                logging.info("Hamza Ilyas ----> Swept Journal Entry Created & posted Successfully")

    def check_ili_in_expenses(self, invoice_line, start_date, end_date):
        logging.info("Hamza Ilyas ----> check_ili_in_expenses Called")
        expenses = self.env['hr.expense'].search([('state', 'in', ('done', 'approved')), '&',
                                                  ('date', '>=', start_date), ('date', '<=', end_date)])
        for expense in expenses:
            # if expense.product_id == invoice_line.product_id and \
            #         expense.analytic_account_id == invoice_line.analytic_account_id and not expense.swept:
            if expense.product_id == invoice_line.product_id and not expense.swept:
                expense.swept = True
                expense.invoice_line_id = invoice_line
                return expense
            else:
                continue

    def check_ili_in_purchase_receipts(self, invoice_line, start_date, end_date):
        logging.info("Hamza Ilyas ----> check_ili_in_purchase_receipts Called")
        purchase_receipts = self.env['account.move'].search(
            [('state', '=', 'posted'), ('move_type', '=', 'in_receipt'), '&',
             ('invoice_date', '>=', start_date), ('invoice_date', '<=', end_date)])
        for receipt in purchase_receipts:
            for receipt_line in receipt.invoice_line_ids:
                # if receipt_line.product_id == invoice_line.product_id and \
                #         receipt_line.analytic_account_id == invoice_line.analytic_account_id and not receipt_line.swept:
                if receipt_line.product_id == invoice_line.product_id and not receipt_line.swept:
                    receipt_line.swept = True
                    receipt_line.invoice_line_id = invoice_line.id
                    return receipt_line
                else:
                    continue

    def check_ili_in_sale_receipts(self, invoice_line, start_date, end_date):
        logging.info("Hamza Ilyas ----> check_ili_in_sale_receipts Called")
        sale_receipts = self.env['account.move'].search([('state', '=', 'posted'), ('move_type', '=', 'out_receipt'),
                                                         '&', ('invoice_date', '>=', start_date),
                                                         ('invoice_date', '<=', end_date)])
        for receipt in sale_receipts:
            for receipt_line in receipt.invoice_line_ids:
                # if receipt_line.product_id == invoice_line.product_id and \
                #         receipt_line.analytic_account_id == invoice_line.analytic_account_id and not receipt_line.swept:
                if receipt_line.product_id == invoice_line.product_id and not receipt_line.swept:
                    receipt_line.swept = True
                    receipt_line.invoice_line_id = invoice_line.id
                    return receipt_line
                else:
                    continue

    def check_ili_in_vendor_bills(self, invoice_line, start_date, end_date):
        logging.info("Hamza Ilyas ----> check_ili_in_vendor_bills Called")
        vendor_bills = self.env['account.move'].search([('state', '=', 'posted'), ('move_type', '=', 'in_invoice'),
                                                        '&', ('invoice_date', '>=', start_date),
                                                        ('invoice_date', '<=', end_date)])
        for bill in vendor_bills:
            for bill_line in bill.invoice_line_ids:
                # if bill_line.product_id == invoice_line.product_id and \
                #         bill_line.analytic_account_id == invoice_line.analytic_account_id and not bill_line.swept:
                if bill_line.product_id == invoice_line.product_id and not bill_line.swept:
                    bill_line.swept = True
                    bill_line.invoice_line_id = invoice_line.id
                    return bill_line
                else:
                    continue


class AccountMoveLineExt(models.Model):
    _inherit = 'account.move.line'

    swept = fields.Boolean(string="Swept", readonly=True)

    invoice_line_id = fields.Many2one("account.move.line", "Invoice Line")

    project_id_hi = fields.Many2one('account.analytic.account', string='Project')

    # line_type = fields.Selection([
    #                             ('out_invoice', 'Customer Invoice'),
    #                             ('in_invoice', 'Vendor Bill'),
    #                             ('out_refund', 'Customer Refund'),
    #                             ('in_refund', 'Vendor Refund')], invisible=True, related='invoice_id.type')

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.move_id.move_type in ['in_invoice', 'in_receipt', 'out_receipt']:
            logging.info("Hamza Ilyas ----> onchange_product_id Called")
            if self.product_id:
                if self.product_id.is_sweep_product:
                    self.account_id = self.product_id.sweep_account_id


class HrExpenseExt(models.Model):
    _inherit = 'hr.expense'

    # product_id = fields.Many2one("product.product", "Product")

    swept = fields.Boolean(string="Swept", readonly=True)
    invoice_line_id = fields.Many2one("account.move.line", "Invoice Line")

    @api.onchange('product_id')
    def onchange_product_id(self):
        logging.info("Hamza Ilyas ----> onchange_product_id Called on hr.expense")
        if self.product_id:
            if self.product_id.is_sweep_product:
                self.account_id = self.product_id.sweep_account_id


# class AccountVoucherExt(models.Model):
#     _inherit = 'account.voucher.line'
#
#     swept = fields.Boolean(string="Swept", readonly=True)
#     invoice_line_id = fields.Many2one("account.move.line", "Invoice Line")
#
#
#     # @api.model
#     # def create(self, vals):
#     #     if 'product_id' in vals:
#     #         if vals['product_id']:
#     #             product = self.env['product.product'].search([('id', '=', vals['product_id'])])
#     #             if product:
#     #                 if product.is_sweep_product and product.sweep_account_id:
#     #                     vals['account_id'] = product.sweep_account_id.id
#     #
#     #     rec = super(AccountVoucherExt, self).create(vals)
#     #     return rec
#
#     #@api.multi
#     # def write(self, vals):
#     #     return super(AccountVoucherExt, self).write(vals)
#
#     @api.onchange('product_id')
#     def onchange_product_id(self):
#         logging.info("Hamza Ilyas ----> onchange_product_id Called on account voucher line")
#         if self.product_id:
#             temp = self.product_id
#             self.product_id = self.env['product.product'].search([])[1]
#             self.product_id = temp
#             if self.product_id.is_sweep_product:
#                 logging.info("Hamza Ilyas ----> is_sweep_product")
#                 self.account_id = self.product_id.sweep_account_id.id
#                 self.write({
#                     'account_id': self.product_id.sweep_account_id.id
#                 })
#                 self.account_id = self.product_id.sweep_account_id.id
#                 logging.info("Hamza Ilyas ----> account_id set as :")
#                 logging.info(self.account_id.name)
#                 # self.check_account_id(self.product_id, self.account_id)
#
#     def check_account_id(self, product_id, account_id):
#         logging.info("Hamza Ilyas ----> check_account_id Called")
#         if product_id.is_sweep_product and product_id.sweep_account_id:
#             logging.info("11")
#             if product_id.sweep_account_id.id != account_id.id:
#                 logging.info("22")
#                 self.onchange_product_id()
#                 logging.info("Hamza Ilyas ----> finish check_account_id")


class SweepJournal(models.Model):
    _name = 'sweep.journal'

    journal_id = fields.Many2one('account.journal', string='Journal')

# class AccountMoveLineExt(models.Model):
#     _inherit = 'account.move.line'
#
#     swept = fields.Boolean(string="Swept", readonly=True)


# class AccountMoveExt(models.Model):
#     _inherit = 'account.move'
#
#     is_a_sweep_je = fields.Boolean()
#     voucher_line_id = fields.Many2one('account.voucher.line', "Voucher Line")
#     vendor_bill_line_id = fields.Many2one('account.move.line', "Vendor Bill Line")
#
#     def button_cancel(self):
#         logging.info("Hamza Ilyas ----> button_cancel Called")
#         for move in self:
#             if not move.journal_id.update_posted:
#                 raise UserError(
#                     _('You cannot modify a posted entry of this journal.\nFirst you should set the journal to allow cancelling entries.'))
#             else:
#                 if move.is_a_sweep_je:
#                     if move.ref:
#                         bill = self.env['account.move'].search([('number', '=', move.ref)])
#                         if bill:
#                             self.unswept_bill_lines(move)
#                         else:
#                             receipt = self.env['account.voucher'].search([('number', '=', move.ref)])
#                             if receipt:
#                                 self.unswept_voucher_lines(move)
#                             else:
#                                 expense = self.env['hr.expense'].search([('name', '=', move.ref)])
#                                 if expense:
#                                     self.unswept_expense(expense)
#                     # for line in move.line_ids:
#                     #     line.swept = False
#
#         if self.ids:
#             self.check_access_rights('write')
#             self.check_access_rule('write')
#             self._check_lock_date()
#             self._cr.execute('UPDATE account_move ' \
#                              'SET state=%s ' \
#                              'WHERE id IN %s', ('draft', tuple(self.ids),))
#             self.invalidate_cache()
#         self._check_lock_date()
#
#         # on cancelling of sweep journal entry it will be removed
#         if self.is_a_sweep_je:
#             logging.info("Hamza Ilyas ----> unlinking swept journal entry")
#             self.unlink()
#         return True
#
#     def unswept_bill_lines(self, move):
#         # for line in bill.invoice_line_ids:
#         #     for move_line in move.line_ids:
#         #         if move_line.product_id.name == line.name and move_line.analytical_account_id == line.account_analytic_id:
#         line = move.vendor_bill_line_id
#         line.swept = False
#         line.invoice_line_id.swept = False
#         line.invoice_id.swept = False
#
#     def unswept_voucher_lines(self, move):
#         # for line in recipt.line_ids:
#         #     for move_line in move.line_ids:
#         #         if move_line.name == line.name and move_line.analytical_account_id == line.account_analytic_id:
#         line = move.voucher_line_id
#         line.swept = False
#         line.invoice_line_id.swept = False
#         line.voucher_id.swept = False
#
#     def unswept_expense(self, expense):
#         expense.swept = False
#         expense.invoice_line_id.swept = False
