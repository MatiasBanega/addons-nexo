
from odoo import fields, models

class Company(models.Model):
    _inherit = 'res.company'

    supplier_document_sign = fields.Many2one('sign.template', string="Document Signed By Vendor", required=True,
        help="Document that the Vendor will have to sign.")

    customer_document_sign = fields.Many2one('sign.template', string="Document Signed By Customer", required=True,
        help="Document that the Customer will have to sign.")
