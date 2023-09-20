from odoo import models, fields, api, _


class HrJob(models.Model):
    _inherit = "hr.job"

    salary_limit_amount = fields.Float(string="Salary Limit", required=True)

