from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class SweepReportXls(models.AbstractModel):
    _name = 'report.sweep_report.sweep_report_xls'
    _inherit = 'report.report_xlsx.abstract'

    # def generate_xlsx_report(self, workbook, data, lines):
    #     print("generate_xlsx_report CALLED XXXXXXXXXXXXXXX")
    #     q = """SELECT AM.DATE,
    #                     AML.SWEPT,
    #                     RP.NAME PARTNER,
    #                     AAA.NAME PROJECT,
    #                     AM.NAME JOURNAL_ENTRY_NUMBER,
    #                     DATE(AM.CREATE_DATE) SWEPT_DATE,
    #                     AM.REF SWEEP_ITEM_JOURNAL_ENTRY_NUMBER,
    #                     AML.NAME SWEPT_ITEM_NAME,
    #                     AML.DEBIT SWEPT_ITEM_DEBIT,
    #                     AML.CREDIT SWEPT_ITEM_CREDIT,
    #                     COALESCE(AIL.NAME) AS UNSWEPT_ITEMS_NAME,
    #                     COALESCE(AIL.PRICE_UNIT) AS UNSWEPT_ITEMS_AMOUNT
    #                 FROM ACCOUNT_MOVE AM
    #                 INNER JOIN ACCOUNT_MOVE_LINE AML ON AM.ID = AML.MOVE_ID
    #                 LEFT OUTER JOIN RES_PARTNER RP ON RP.ID = AML.PARTNER_ID
    #                 LEFT OUTER JOIN ACCOUNT_ANALYTIC_ACCOUNT AAA ON AAA.ID = AML.PROJECT_ID
    #                 LEFT OUTER JOIN ACCOUNT_MOVE AI ON AI.NAME = AM.REF
    #                 LEFT OUTER JOIN ACCOUNT_MOVE_LINE AIL ON AI.ID = AIL.MOVE_ID
    #                 AND AIL.SWEPT = FALSE
    #                 WHERE AM.IS_A_SWEEP_JE = TRUE
    #                     AND AM.DATE BETWEEN '{0}' AND '{1}'
    #                 ORDER BY 1;""".format(
    #         datetime.strptime(data['start_date'], '%Y-%m-%d').date(),
    #         datetime.strptime(data['end_date'], '%Y-%m-%d').date())
    #     print(q)
    #     self.env.cr.execute(q)
    #
    #     sheet = workbook.add_worksheet('Sweep Report')
    #     bold = workbook.add_format({'bold': True})
    #     format = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True})
    #     format1 = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': 'yellow'})
    #     sheet.set_column(1, 0, 15)
    #     sheet.write(1, 0, 'Date Range', format)
    #     sheet.set_column(1, 1, 25)
    #     sheet.write(1, 1, 'Partner', format)
    #     sheet.set_column(1, 2, 25)
    #     sheet.write(1, 2, 'Project', format)
    #     sheet.set_column(1, 3, 30)
    #     sheet.write(1, 3, 'Sweep Journal Entry', format)
    #     sheet.set_column(1, 4, 30)
    #     sheet.write(1, 4, 'Item Journal Entry', format)
    #     # sheet.set_column(0, 4, 35)
    #     sheet.merge_range(0, 5, 0, 6, 'Swept Items', format1)
    #     sheet.merge_range(0, 7, 0, 8, 'Unswept Items', format1)
    #     # sheet.write(0, 4, 'Swept Items', format)
    #     sheet.set_column(1, 7, 25)
    #     sheet.write(1, 5, 'Name', format)
    #     sheet.write(1, 6, 'Amount', format)
    #     sheet.write(1, 7, 'Name', format)
    #     sheet.write(1, 8, 'Amount', format)
    #     sheet.set_column(1, 9, 25)
    #     sheet.write(1, 9, 'Date Swept', format)
    #     res = self.env.cr.dictfetchall()
    #     col = 0
    #     row = 2
    #     for i in res:
    #         name = amount = ""
    #         logging.info("Hamza I -----> str(i.get('sweep_item_journal_entry_number')) : ")
    #         logging.info(str(i.get('sweep_item_journal_entry_number')))
    #         if str(i.get('journal_entry_number')):
    #             name, amount = self.find_ref_usi(str(i.get('journal_entry_number')))
    #         sheet.write(row, col, str(i.get('date')))
    #         sheet.write(row, col + 1, str(i.get('partner')))
    #         sheet.write(row, col + 2, str(i.get('project')))
    #         sheet.write(row, col + 3, str(i.get('journal_entry_number')))
    #         sheet.write(row, col + 4, str(i.get('sweep_item_journal_entry_number')))
    #         sheet.write(row, col + 5, str(i.get('swept_item_name')))
    #         sheet.write(row, col + 6, str(i.get('swept_item_debit')) if i.get('swept_item_debit') > 0.0 else (-i.get('swept_item_credit')))
    #         sheet.write(row, col + 7, str(name))
    #         sheet.write(row, col + 8, str(amount))
    #         sheet.write(row, col + 9, str(i.get('swept_date')))
    #         row += 1

    def generate_xlsx_report(self, workbook, data, lines):
        print("generate_xlsx_report CALLED XXXXXXXXXXXXXXX")
        q = """SELECT AM.DATE,
                        AML.SWEPT,
                        RP.NAME PARTNER,
                        AAA.NAME PROJECT,
                        AM.NAME JOURNAL_ENTRY_NUMBER,
                        DATE(AM.CREATE_DATE) SWEPT_DATE,
                        AM.REF SWEEP_ITEM_JOURNAL_ENTRY_NUMBER,
                        AML.NAME SWEPT_ITEM_NAME,
                        AML.DEBIT SWEPT_ITEM_DEBIT,
                        AML.CREDIT SWEPT_ITEM_CREDIT,
                        COALESCE(AIL.NAME) AS UNSWEPT_ITEMS_NAME,
                        COALESCE(AIL.PRICE_UNIT) AS UNSWEPT_ITEMS_AMOUNT
                    FROM ACCOUNT_MOVE AM
                    INNER JOIN ACCOUNT_MOVE_LINE AML ON AM.ID = AML.MOVE_ID
                    LEFT OUTER JOIN RES_PARTNER RP ON RP.ID = AML.PARTNER_ID
                    LEFT OUTER JOIN ACCOUNT_ANALYTIC_ACCOUNT AAA ON AAA.ID = AML.PROJECT_ID_HI
                    LEFT OUTER JOIN ACCOUNT_MOVE AI ON AI.NAME = AM.REF
                    LEFT OUTER JOIN ACCOUNT_MOVE_LINE AIL ON AI.ID = AIL.MOVE_ID
                    AND AIL.SWEPT = FALSE
                    WHERE AM.IS_A_SWEEP_JE = TRUE
                        AND AM.DATE BETWEEN '{0}' AND '{1}'
                    ORDER BY 1;""".format(
            datetime.strptime(data['start_date'], '%Y-%m-%d').date(),
            datetime.strptime(data['end_date'], '%Y-%m-%d').date())
        print(q)
        self.env.cr.execute(q)

        sheet = workbook.add_worksheet('Sweep Report')
        bold = workbook.add_format({'bold': True})
        format = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True})
        format1 = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': 'yellow'})
        sheet.set_column(1, 0, 15)
        sheet.write(1, 0, 'Date Range', format)
        sheet.set_column(1, 1, 25)
        sheet.write(1, 1, 'Partner', format)
        sheet.set_column(1, 2, 25)
        sheet.write(1, 2, 'Project', format)
        sheet.set_column(1, 3, 30)
        sheet.write(1, 3, 'Sweep Journal Entry', format)
        sheet.set_column(1, 4, 30)
        sheet.write(1, 4, 'Item Journal Entry', format)
        sheet.merge_range(0, 5, 0, 7, 'Swept Items', format1)
        sheet.merge_range(0, 8, 0, 9, 'Unswept Items', format1)
        sheet.write(1, 5, 'Name', format)
        sheet.write(1, 6, 'Debit', format)  # Debit column
        sheet.write(1, 7, 'Credit', format)  # Credit column
        sheet.write(1, 8, 'Name', format)
        sheet.write(1, 9, 'Amount', format)
        sheet.set_column(1, 10, 25)
        sheet.write(1, 10, 'Date Swept', format)

        res = self.env.cr.dictfetchall()
        col = 0
        row = 2
        for i in res:
            name = amount = ""
            logging.info("Hamza I -----> str(i.get('sweep_item_journal_entry_number')) : ")
            logging.info(str(i.get('sweep_item_journal_entry_number')))
            if str(i.get('journal_entry_number')):
                name, amount = self.find_ref_usi(str(i.get('journal_entry_number')))
            sheet.write(row, col, str(i.get('date')))
            sheet.write(row, col + 1, str(i.get('partner')))
            sheet.write(row, col + 2, str(i.get('project')))
            sheet.write(row, col + 3, str(i.get('journal_entry_number')))
            sheet.write(row, col + 4, str(i.get('sweep_item_journal_entry_number')))
            sheet.write(row, col + 5, str(i.get('swept_item_name')))
            # Write Debit and Credit in separate columns
            debit = i.get('swept_item_debit') if i.get('swept_item_debit') > 0.0 else 0.0
            credit = -i.get('swept_item_credit') if i.get('swept_item_credit') > 0.0 else 0.0
            sheet.write(row, col + 6, str(debit))
            sheet.write(row, col + 7, str(credit))
            # Shift your other columns over by 1 to accommodate the added column
            sheet.write(row, col + 8, str(name))
            sheet.write(row, col + 9, str(amount))
            sheet.write(row, col + 10, str(i.get('swept_date')))
            row += 1

    def find_ref_usi(self, move_num):
        if move_num:
            logging.info("find_ref_usi ---- move_num")
            logging.info(move_num)
            je = self.env['account.move'].search([('name', '=', move_num)])
            if je:
                logging.info("move found")
                if je.ref_line_id:
                    logging.info("<<<<<<<<<<<<<<<<<Vendor bill lines>>>>>>>>>>>>>>>>>")
                    logging.info(repr(je.ref_line_id.move_id.invoice_line_ids))
                    for line in je.ref_line_id.move_id.invoice_line_ids:
                        if not line.swept:
                            return line.name, line.price_unit
                # if je.voucher_line_id:
                #     logging.info("<<<<<<<<<<<<<<<<<<Voucher lines>>>>>>>>>>>>>>>>>>")
                #     logging.info(repr(je.voucher_line_id.voucher_id.line_ids))
                #     for line in je.voucher_line_id.voucher_id.line_ids:
                #         if not line.swept:
                #             return line.name, line.price_unit
        return 'N/A', 'N/A'

            #     return self.get_name_amount_from_bill(bill.invoice_line_ids)
            # else:
            #     receipt = self.env['account.voucher'].search([('number', '=', ref)])
            #     if receipt:
            #         logging.info("Receipt ref")
            #         return self.get_name_amount_from_receipt(receipt.line_ids)
                # else:
                #     expense = self.env['hr.expense'].search([('name', '=', ref)])
                #     if expense:
                #         self.unswept_expense(expense)

    # def get_name_amount_from_bill(self, bill_lines):
    #     for line in bill_lines:
    #         if not line.swept:
    #             return line.name, line.price_unit
    #         return 'N/A', 'N/A'
    #
    # def get_name_amount_from_receipt(self, receipt_lines):
    #     for line in receipt_lines:
    #         if not line.swept:
    #             return line.name, line.price_unit
    #         return 'N/A', 'N/A'

# SweepReportXls('report.sweep_report.report_sweep_report.xlsx', 'sweep.report')
