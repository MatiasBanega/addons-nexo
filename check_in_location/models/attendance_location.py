from odoo import models, fields, tools, api

class HrAttendanceLocation(models.Model):
    _name = 'hr.attendance.location'

    sequence = fields.Integer("Sequence")
    code = fields.Char('Code', required=True)
    name = fields.Char('Name', required=True)
    loc_class_name = fields.Char('Class Name')