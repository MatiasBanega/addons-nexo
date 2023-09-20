from odoo import models, api, fields


class StockPurchaseOrder(models.Model):
    _inherit = "purchase.order"

    job_id = fields.Many2one("project.project", string="Job ID")
