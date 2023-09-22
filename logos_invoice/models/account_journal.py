# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class AccountJournal(models.Model):

    _inherit = "account.journal"

    logo = fields.Image(string="Logo")
