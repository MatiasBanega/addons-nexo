# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

import logging

log = logging.getLogger(__name__)

class HrContract(models.Model):
    _inherit = 'hr.contract'
     
    def _get_default_value(self):
        res = self.env.company.currency_id
        return res
        
    currency_id = fields.Many2one('res.currency', related='', string="Currency", required=True, readonly=False, default=_get_default_value)

 