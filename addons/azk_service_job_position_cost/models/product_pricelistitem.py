from odoo import models, fields, api, _


class ProductPriceListItem(models.Model):
    _inherit = "product.pricelist.item"
    
    base = fields.Selection(selection_add=[('designation_cost', 'Designation Cost')], ondelete={'designation_cost': 'set default'})
