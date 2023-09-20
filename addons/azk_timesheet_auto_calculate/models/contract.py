from odoo import models, fields, api
from datetime import date

class HrContract(models.Model):
    _inherit = 'hr.contract'
    
    recalculate = fields.Integer(string="Recalculate", readonly=True)
    salary_time_sheet = fields.Float(string="Total Salary For Hourly Time Sheet Cost", compute="_compute_salary_time_sheet", store=True)
    company_currency_id = fields.Many2one(related='company_id.currency_id', store=True)

    @api.depends('company_id','recalculate','company_id.computed_fields_hourly_cost','company_id.hourly_rate_factor')
    def _compute_salary_time_sheet(self):
        for rec in self:
            total = 0
            for field in rec.company_id.computed_fields_hourly_cost:
                total += rec[field.name]
            rec.salary_time_sheet  = rec.currency_id._convert(total, rec.company_currency_id, rec.company_id, date.today())
            if rec.company_id.hourly_rate_factor > 0 and  rec.employee_id.contract_id.filtered(lambda a: a.state == 'open' ) and rec.employee_id.calculate_salary_based == True:
                rec.employee_id.timesheet_cost = rec.salary_time_sheet / rec.company_id.hourly_rate_factor
     
    def write(self, vals):
        for rec in self:
            recalculate = rec.recalculate + 1
            vals['recalculate'] = recalculate
        res = super().write(vals)
        return res
    
    @api.onchange('state')
    def onchange_state(self):
        if self.state == 'open' and self.employee_id:
            self.employee_id.calculate_salary_based = True
            