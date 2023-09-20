from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"
    
    hourly_rate_factor =  fields.Float(related="company_id.hourly_rate_factor",string="Hourly Rate Factor",readonly=False,store=True)
  
    @api.onchange('hourly_rate_factor')
    def onchange_hourly_rate_factor(self):
        if self.hourly_rate_factor <= 0:
            raise UserError(_('Cannot add Zero or Negative Value'))