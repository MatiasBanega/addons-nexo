
import calendar
from odoo import api, fields, models, _


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    bussiness_days_count = fields.Integer(string="Bussines Days", compute="_compute_bussiness_days_count")

    @api.depends("date_to", "date_from")
    def _compute_bussiness_days_count(self):
        weekday_count = 0
        cal = calendar.Calendar()

        for week in cal.monthdayscalendar(self.date_from.year, self.date_from.month):
            for i, day in enumerate(week):
                # not this month's day or a weekend
                if day == 0 or i >= 5:
                    continue
                # or some other control if desired...
                weekday_count += 1
        self.bussiness_days_count = weekday_count