# -*- coding: utf-8 -*-
# Iheb Ltaief

from odoo import fields, models, api


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def _prepare_line_values(self, line, account_id, date, debit, credit):
        # print('partner', line.partner_id.name)
        # print('line', line.id)
        return {
            'name': line.name,
            'partner_id': line.slip_id.employee_id.address_home_id.id if line.salary_rule_id.affect_partner else line.partner_id.id,
            'account_id': account_id,
            'journal_id': line.slip_id.struct_id.journal_id.id,
            'date': date,
            'debit': debit,
            'credit': credit,
            'analytic_account_id': line.slip_id.contract_id.analytic_account_id.id if (self.env['account.account'].browse(account_id).user_type_id.internal_group == 'expense') else line.salary_rule_id.analytic_account_id.id,
        }

    def _get_existing_lines(self, line_ids, line, account_id, debit, credit):
        # print(line.read())
        print(self.env['account.account'].browse(account_id).user_type_id.internal_group)
        # for line_id in line_ids:
            # print(line_id)
        existing_lines = (
            line_id for line_id in line_ids if
            line_id['name'] == line.name
            and line_id['account_id'] == account_id
            and ((not line.salary_rule_id.affect_partner) and (not line_id['partner_id']))
            and (line_id['analytic_account_id'] == (line.salary_rule_id.analytic_account_id.id or line.slip_id.contract_id.analytic_account_id.id))
            and ((line_id['debit'] > 0 and credit <= 0) or (line_id['credit'] > 0 and debit <= 0)))
        return next(existing_lines, False)


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    affect_partner = fields.Boolean(string='Affect Partner')
