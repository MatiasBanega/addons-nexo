#-*- coding:utf-8 -*-

from odoo import api, fields, models, tools, _


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    employee_id = fields.Many2one("hr.employee", string="Employee")