# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    api_token_expiration = fields.Integer(string='Api Token Expiration (m)', default=0, help='Set the expiry time in minutes for the API token calls for Azkatech authenticated API. Set zero to disable')
    
    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param('az_lead_extract_auth.api_token_expiration', self.api_token_expiration)
      
        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        res.update(
           api_token_expiration = int(ICPSudo.get_param('az_lead_extract_auth.api_token_expiration')),
          
           )
        return res
   