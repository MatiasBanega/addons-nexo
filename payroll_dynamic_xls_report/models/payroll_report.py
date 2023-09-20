from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class payrollReport(models.Model):
    _name = 'payroll.report'
    _descripion = 'Payroll Report'
    _rec_name = 'report_title'

    rule_ids = fields.Many2many("hr.salary.rule", string="Salary Rules", required=True)
    report_title = fields.Char("Report Title")
