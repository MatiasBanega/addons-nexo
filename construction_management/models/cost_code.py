# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp


class cost_code(models.Model):
    _name = 'cost.code'
    _description = 'Cost Code'

    number = fields.Integer("Cost Header Number", required=True, )
    name = fields.Char("Cost Header Name", required=True, size=64, )
    description = fields.Char("Description", required=True, size=64, )
    price_unit = fields.Float(
        "Unit Price", digits='Account', )
    qty = fields.Float("Qty", default=1)
    cost_code_id = fields.Many2one(
        'cost.header', "Cost Code")
