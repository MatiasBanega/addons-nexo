from urllib.parse import urlencode, urljoin

from odoo import api, fields, models
from odoo.exceptions import ValidationError

class ResBankAccount(models.Model):
    _name = "res.bank.account"
    _inherit = "res.partner.bank"

    partner_id = fields.Many2one(comodel_name="res.partner", required=False)
    acc_holder_name = fields.Char(required=True)
    description = fields.Char(string="Description", default="Kindly make payment into this below account", required=True)
    sortcode = fields.Char(string="Sort Code")

