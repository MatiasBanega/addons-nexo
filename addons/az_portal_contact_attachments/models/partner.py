from odoo import api, fields, models, _
import logging
log = logging.getLogger(__name__)

class Partner(models.Model):
    _inherit = 'res.partner'
    
    total_portal_document = fields.Integer('Portal Document', compute="_compute_total_portal_documents")
    
   
    def _compute_total_portal_documents(self):
       for rec in self:
           partner_id = rec
           if partner_id.company_type == 'person' and partner_id.parent_id:
               partner_id = partner_id.parent_id
           rec.total_portal_document = self.env['ir.attachment'].search_count([('res_id', '=', partner_id.id), ('portal', '=', True)])
           
           
    def action_view_portal_document(self):
        self.ensure_one()
        partner_id = self
        if partner_id.company_type == 'person' and partner_id.parent_id:
            partner_id = partner_id.parent_id
        action = {
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'name': _('Portal Document %s', self.name),
            'domain': [('res_id', '=', partner_id.id), ('portal', '=', True)],
        }
       
        return action
                