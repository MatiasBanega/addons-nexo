#-*- coding:utf-8 -*-

from odoo import fields, models


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    def _get_existing_lines(self, line_ids, line, account_id, debit, credit):
        if line.salary_rule_id.display_split:
            return False
        else:
            return super(HrPayslip, self)._get_existing_lines(line_ids, line, account_id, debit, credit)

    def _prepare_line_values(self, line, account_id, date, debit, credit):
        if line.salary_rule_id.display_split:
            return {
                'name': line.name,
                'partner_id': line.partner_id.id or line.slip_id.employee_id.user_id.partner_id.id,
                'account_id': account_id,
                'employee_id': line.slip_id.employee_id.id,
                'journal_id': line.slip_id.struct_id.journal_id.id,
                'date': date,
                'debit': debit,
                'credit': credit,
                'analytic_account_id': line.salary_rule_id.analytic_account_id.id or line.slip_id.contract_id.analytic_account_id.id,
            }
        else:
            return super(HrPayslip, self)._prepare_line_values(line, account_id, date, debit, credit)
