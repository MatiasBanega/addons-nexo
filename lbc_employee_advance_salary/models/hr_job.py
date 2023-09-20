from odoo import models, fields, api


class HrJob(models.Model):
    _inherit = "hr.job"

    salary_limit_amount = fields.Float(string="Salary Advance Limit", required=True)
