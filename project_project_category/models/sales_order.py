from odoo import models, api, fields


class StockSaleOrder(models.Model):
    _inherit = "sale.order"

    job_id = fields.Many2one("project.project", string="Job ID")
