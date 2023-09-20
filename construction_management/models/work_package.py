# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp


class work_package(models.Model):
    _name = 'work.package'
    _description = 'Work Packages'

    @api.depends('cost_header_ids.cost_of_header')
    def _compute_amount(self):
        total = 0.0
        for cost_header in self.cost_header_ids:
            total += cost_header.cost_of_header
        self.work_package_cost = total

    name = fields.Char("Work Package Name", size=64, required=True, )
    work_package_cost = fields.Float(
        'Work Package Cost', compute='_compute_amount',
        readonly=True, store=True,
        digits='Account', )
    cost_header_ids = fields.Many2many(
        'cost.header', 'work_package_cost_header_rel', 'work_package_id',
        'cost_header_id', 'Cost Header')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
