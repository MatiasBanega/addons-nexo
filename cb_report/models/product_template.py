from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):

    _inherit = "product.template"


    product_duty = fields.Boolean(string='Duty')
    shipping_charge = fields.Boolean(string='Shipping')
    terminal_charge = fields.Boolean(string='Terminal')
    nafdac = fields.Boolean(string='Nafdac')
    son = fields.Boolean(string='SON')
    agency = fields.Boolean(string='Agency')
    transportation = fields.Boolean(string="Transportation")
    others = fields.Boolean(string="Others")


