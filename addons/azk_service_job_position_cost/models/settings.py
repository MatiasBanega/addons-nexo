from odoo import models, fields, api, _


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"
    
    designation_cost_calculate = fields.Selection(related="company_id.designation_cost_calculate",string="Designation Cost Calculation",store=True, readonly =False)
  
    