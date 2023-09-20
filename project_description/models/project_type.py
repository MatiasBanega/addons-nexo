from odoo import fields, models, api


class ProjectTypeInherited(models.Model):
    _inherit = "project.type"

    related_products_ids = fields.One2many("product.template", "project_type_id", "Related Products")
