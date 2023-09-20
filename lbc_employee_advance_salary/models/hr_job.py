from odoo import models, fields, api


class HrJob(models.Model):
    _inherit = "hr.job"

<<<<<<< HEAD
    salary_limit_amount = fields.Float(string="Salary Advance Limit", required=True)
=======
    salary_limit_amount = fields.Float(string="Salary Advance Limit", required=True)
>>>>>>> main
