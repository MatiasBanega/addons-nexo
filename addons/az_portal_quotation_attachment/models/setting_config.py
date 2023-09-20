import logging
from odoo import api, fields, models, _

log = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = 'res.company'
    
    portal_sale_attachemnt_warning = fields.Text('Portal Quotation Attachment Warning')
    
class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    portal_sale_attachemnt_warning = fields.Text('Portal Quotation Attachment Warning', 
                                                  related='company_id.portal_sale_attachemnt_warning',
                                                  readonly=False)
