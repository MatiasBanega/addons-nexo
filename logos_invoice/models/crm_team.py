# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CrmTeam(models.Model):
    _inherit = 'crm.team'
    logo = fields.Image(string="Logo")



