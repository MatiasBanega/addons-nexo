# -*- coding:utf-8 -*-

from odoo import fields, models


class HrSalaryRule(models.Model):
	_inherit = 'hr.salary.rule'

	display_split = fields.Boolean(string="Split Lines")
