
from odoo import models, fields, api, _

class Partner(models.Model):
    _inherit = 'res.partner'
    
    @api.onchange('parent_id')
    def on_change_parent_for_company_name(self):
        if self.parent_id:
            self.company_name = self.parent_id.name
        else:
            self.company_name = False
 
    def write(self, vals):
        res = super().write(vals)

        for record in self:
            if 'x_studio_trade_license_expiry' in vals and record.company_type == 'person' and record.parent_id and not record._context.get('parent_update'):
                record.parent_id.x_studio_trade_license_expiry = record.x_studio_trade_license_expiry
                
            if 'x_studio_trade_license_number' in vals and record.company_type == 'person' and record.parent_id and not record._context.get('parent_update'):
                record.parent_id.x_studio_trade_license_number = record.x_studio_trade_license_number

            childs = self.env['res.partner'].search([('parent_id', '=', record.id)])  
            if 'x_studio_trade_license_expiry' in vals and childs:
                for rec in childs:
                    rec.with_context(parent_update = True).x_studio_trade_license_expiry = self.x_studio_trade_license_expiry
             
            if 'x_studio_trade_license_number' in vals and childs:
                for rec in childs:
                    rec.with_context(parent_update = True).x_studio_trade_license_number = self.x_studio_trade_license_number
                     
            if 'parent_id' in vals and self.parent_id:
                self.company_name = self.parent_id.name
        return res
    
    @api.model
    def create(self, vals):
        res = super().create(vals)
        for rec in res:
            if 'parent_id' in vals and rec.parent_id:
                    rec.company_name = rec.parent_id.name
                
        return res 