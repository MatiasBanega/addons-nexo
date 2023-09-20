from odoo import fields, models, api


class ProductTemplateExt(models.Model):
    _inherit = "product.template"

    is_project_item = fields.Boolean("Delivery Item", default=False, help="This is a project delivery items")
    project_type_id = fields.Many2one("project.type", "Project Type")


class ProductUnitOfMeasureExt(models.Model):
    _inherit = "uom.uom"

    unit_measured_as = fields.Selection(
        [("wgt", "Weight"), ("size", "Size")],
        "Measured as",
        default="size",
        help="This will help in analysis of the project/Job report",
    )
