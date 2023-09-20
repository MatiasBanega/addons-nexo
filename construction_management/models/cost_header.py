# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp


class cost_header(models.Model):
    _name = 'cost.header'
    _description = 'Cost Header'

    @api.depends('cost_code_ids.price_unit', 'cost_code_ids.qty')
    def _compute_amount(self):
        cost = 0.0
        for cost_code_line in self.cost_code_ids:
            cost = cost + (cost_code_line.price_unit * cost_code_line.qty)
        self.cost_of_header = cost

    number = fields.Integer("Cost Header Number", required=True, )
    name = fields.Char("Cost Header Name", required=True, size=64, )
    cost_of_header = fields.Float(
        'Cost Of Header', compute='_compute_amount',
        readonly=True, store=True,
        digits='Account', )
    cost_code_ids = fields.Many2many(
        'cost.code', 'cost_code_id', string="Cost Code")
