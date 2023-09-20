from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = "hr.employee"
    
    calculate_salary_based = fields.Boolean(string="Calculate Based On Salary ",default=True)
    