import logging
from odoo import api, fields, models, _
import uuid
log = logging.getLogger(__name__)

class IRAttachment(models.Model):
    _inherit = 'ir.attachment'
    
    portal = fields.Boolean('Portal')
    
   
    def write(self, vals):
        res = super().write(vals)
        if 'portal' in vals and self.portal == True and not self.access_token:
            self.access_token = str(uuid.uuid4())
            
        return res
    
    @api.model_create_multi
    def create(self, vals):
        res = super().create(vals)
        
        for rec in res:
            if rec.portal:
                if self._context.get('active_model') == 'res.partner' and self._context.get('active_id'):
                    rec.res_model = 'res.partner'
                    rec.res_id = int(self._context.get('active_id'))
                if not rec.access_token:
                    rec.access_token = str(uuid.uuid4())
                
        return res
                