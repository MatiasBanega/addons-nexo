from odoo import fields, models, api


class ResUsers(models.Model):
    _inherit = "res.users"

    def _get_related_employees(self):
        return self.employee_id