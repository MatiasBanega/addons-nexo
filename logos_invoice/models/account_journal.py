# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class AccountJournal(models.Model):

    _inherit = "account.journal"

    logo = fields.Image(string="Logo")
    street = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict',
                               domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')