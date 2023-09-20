import logging
from odoo import api, fields, models, _

log = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = 'res.company'
    
    restrict_rfq_sub_after_sub_date = fields.Boolean('Restrict RFQ Submission after Submission Date')
    
class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
  
    restrict_rfq_sub_after_sub_date = fields.Boolean('Restrict RFQ Submission after Submission Date', 
                                                  related='company_id.restrict_rfq_sub_after_sub_date',
                                                  readonly=False)
