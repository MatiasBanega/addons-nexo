from odoo import models, fields, tools, api
from datetime import datetime
import pytz
class BHHrAttendance(models.Model):
    _inherit = 'hr.attendance'

    attendance_location = fields.Many2one('hr.attendance.location', 'Check in location', default=lambda self: self.env.ref('check_in_location.attendance_location_company', raise_if_not_found=False))

    @api.model
    def create(self, values):
        if self.env.context.get('current_location'):
            values['attendance_location'] = self.env.context.get('current_location')

        return super(BHHrAttendance, self).create(values)



