# -*- coding: utf-8 -*-

# from openerp import models, fields, api, _
from odoo import models, fields, api, _


class hr_employee(models.Model):
    _inherit = "hr.employee"

    advance_ids = fields.One2many(
        "employee.advance.salary", "employee_id", string="Advance Salary Requests"
    )

    def get_advance_salary(self, emp_id, date_from, date_to=None):
        if date_to is None:
            date_to = datetime.now().strftime("%Y-%m-%d")

        self._cr.execute(
            "SELECT sum(o.request_amount) from employee_advance_salary as o where \
                            o.employee_id=%s \
                            and o.state='done' \
                            AND o.account_validate_date >= %s AND o.account_validate_date <= %s ",
            (emp_id, date_from, date_to),
        )
        res = self._cr.fetchone()
        return res and res[0] or 0.0
