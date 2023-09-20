from odoo import fields, models, api


class ProjectSalesOrder(models.Model):
    _inherit = "sale.order"

    project_items_ids = fields.One2many(
        "project.schedule.items",
        "project_order_id",
        "Project Items",
    )

    job_id = fields.Many2one("project.project", string="Job ID")
