# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrEmployeePublicError(models.Model):
    _inherit = 'hr.employee'

    other = fields.Char()
    device_id = fields.Char()


