
from odoo import fields, models,api ,Command

class PortalWizard(models.TransientModel):

    _inherit = 'portal.wizard'
    _description = 'Grant Portal Access'

    def _default_custom_partner_ids(self):
        active_model = self.env.context.get('active_model', [])
        if active_model  == 'sale.order' or active_model == 'purchase.order':
            id = self.env.context.get('active_ids', [])
            if active_model  == 'sale.order':
                partner = self.env['sale.order'].search([('id','=',id)]).partner_id
            else:
                 partner = self.env['purchase.order'].search([('id','=',id)]).partner_id
            res = partner.child_ids.filtered(lambda p: p.type in ('contact', 'other')) | partner
        else:
            res = super()._default_partner_ids()
        return res

    partner_ids = fields.Many2many(default=_default_custom_partner_ids)
    
           