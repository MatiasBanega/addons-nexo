from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

log = logging.getLogger(__name__)

class VendorRatingElement(models.Model):
    _name = 'vendor.rating.element'
    _description = 'Vendor Rating Element'
    
    name = fields.Char('Rating Element', required=True)
    max_rate = fields.Float('Maximum Rate', required=True)
    active = fields.Boolean('Active', default=True)
    
    @api.constrains('max_rate')
    def _validate_max_rate(self):
        for rec in self:
            if rec.max_rate <= 0:
                raise ValidationError("Maximum Rate must be greater than 0")
    

class VendorRating(models.Model):
    _name = 'vendor.rating'
    _description = 'Vendor Rating'
    
    vendor_id = fields.Many2one('res.partner', string='Vendor')
    rating_element_id = fields.Many2one('vendor.rating.element', string='Rating Element')
    max_rate = fields.Float(related='rating_element_id.max_rate')
    rate = fields.Float('Rate')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    po_rating_ids = fields.One2many('purchase.order.rating', 'vendor_rating_id', string="PO Rating Details")
    
#     def view_po_list(self):
#         self.ensure_one()
#         partner_id = self.vendor_id
#         
#         action = {
#             'res_model': 'purchase.order',
#             'type': 'ir.actions.act_window',
#             'view_mode': 'tree,form',
#             'name': _('Vendor Rating POs  %s', partner_id.name),
#             'domain': [('partner_id', '=', partner_id.id), ('company_id', '=', self.company_id.id), ('po_rating_ids', '!=', False)],
#         }
#        
#         return action
#     
    
class PORating(models.Model):
    _name = 'purchase.order.rating'
    _description = 'Purchase Order Rating'
    
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order', required=True)
    vendor_id = fields.Many2one('res.partner', related='purchase_order_id.partner_id', strore=True, string='Supplier')
    rating_element_id = fields.Many2one('vendor.rating.element', string='Rating Element', required=True)
    max_rate = fields.Float(related='rating_element_id.max_rate')
    rate = fields.Float('Rate')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    vendor_rating_id = fields.Many2one('vendor.rating', string="Vendor Rating")
    
    @api.constrains('rate')
    def _validate_rate(self):
        for rec in self:
            if rec.rate <= 0:
                raise ValidationError("Rate must be greater than 0")
            if rec.rate and rec.rate > rec.max_rate:
                raise ValidationError(_("Rate must be less or equal to %s") % (rec.max_rate))
    
    @api.constrains('rating_element_id')
    def _validate_element(self):
        for rec in self:
            if self.env['purchase.order.rating'].search_count([('rating_element_id' ,'=', rec.rating_element_id.id), ('purchase_order_id', '=', rec.purchase_order_id.id), ('company_id', '=', rec.company_id.id)]) > 1:
                raise ValidationError("Rating element already exists.")
            
    

    
    @api.model
    def create(self, vals):
        record = super().create(vals)
        
        for rec in record:
            rating_line = self.env['vendor.rating'].sudo().search([('vendor_id', '=', rec.vendor_id.id), ('rating_element_id','=', rec.rating_element_id.id)
                                                                   ,('company_id', '=', rec.company_id.id)])
            if rating_line:
                po_rating = self.env['purchase.order.rating'].sudo().search([('vendor_id', '=', rec.vendor_id.id),('company_id', '=', rec.company_id.id)
                                                                             ,('rating_element_id', '=', rec.rating_element_id.id)])
                
                rating_line.rate = (sum(po_rating.mapped('rate')) / len(po_rating)) / rec.rating_element_id.max_rate
                rec.vendor_rating_id = rating_line.id
            else:
                vr = self.env['vendor.rating'].create({
                                                    'vendor_id': rec.vendor_id.id,
                                                    'rating_element_id': rec.rating_element_id.id,
                                                    'rate': rec.rate / rec.rating_element_id.max_rate,
                                                })
                rec.vendor_rating_id = vr.id
        
        return record
    
    
    def write(self, vals):
        record = super().write(vals)
        
        for rec in self:
            rating_line = self.env['vendor.rating'].sudo().search([('vendor_id', '=', rec.vendor_id.id), ('rating_element_id','=', rec.rating_element_id.id)
                                                                   ,('company_id', '=', rec.company_id.id)])

            po_rating = self.env['purchase.order.rating'].sudo().search([('vendor_id', '=', rec.vendor_id.id),('company_id', '=', rec.company_id.id)
                                                                         ,('rating_element_id', '=', rec.rating_element_id.id)])
            
            rating_line.rate = (sum(po_rating.mapped('rate')) / len(po_rating)) / rec.rating_element_id.max_rate

        return record
    
    def unlink(self):
        for rec in self:
            rating_line = self.env['vendor.rating'].sudo().search([('vendor_id', '=', rec.vendor_id.id), ('rating_element_id','=', rec.rating_element_id.id)
                                                                   ,('company_id', '=', rec.company_id.id)])
            
            po_rating = self.env['purchase.order.rating'].sudo().search([('vendor_id', '=', rec.vendor_id.id),('company_id', '=', rec.company_id.id)
                                                                        ,('rating_element_id', '=', rec.rating_element_id.id), ('id', '!=' , rec.id)])
            if not po_rating:
                rating_line.unlink()
            else:
                rating_line.rate = (sum(po_rating.mapped('rate')) / len(po_rating)) / rec.rating_element_id.max_rate
            
        return super().unlink()
    
    
class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
 
    po_rating_ids = fields.One2many('purchase.order.rating', 'purchase_order_id')
    po_rating_count = fields.Integer('Rating Count', compute='_compute_po_rating_count')
    

    def _compute_po_rating_count(self):
        for rec in self:
            rec.po_rating_count = len(rec.po_rating_ids)
            
            
    def create_vendor_rating_elements(self):
        self.ensure_one()
        elemnts = self.env['vendor.rating.element'].search([])
        vals = []
        
        for el in elemnts:
            vals.append({
                            'vendor_id': self.partner_id.id,
                            'rating_element_id': el.id,
                            'purchase_order_id': self.id
                        })
        self.env['purchase.order.rating'].create(vals)
        
        return self.action_view_po_rating()
            
            
            
    def action_view_po_rating(self):
        self.ensure_one()
        partner_id = self
        
        action = {
            'res_model': 'purchase.order.rating',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'name': _('PO Rating %s', self.name),
            'domain': [('purchase_order_id', '=', self.id), ('company_id', '=', self.company_id.id)],
            'context': "{'default_vendor_id': %s, 'default_purchase_order_id': %s}" % (self.partner_id.id,self.id)
        }
       
        return action
    
    
class ResPartner(models.Model):
    _inherit = 'res.partner'
 
    vendor_rating_ids = fields.One2many('vendor.rating', 'vendor_id')
    vendor_rating_count = fields.Integer('Rating Count', compute='_compute_vendor_rating_count')
    

    def _compute_vendor_rating_count(self):
        for rec in self:
            rec.vendor_rating_count = len(rec.vendor_rating_ids)
            
    
   
    def action_view_vendor_rating(self):
        self.ensure_one()
        partner_id = self
        
        action = {
            'res_model': 'vendor.rating',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'name': _('Vendor Rating %s', self.name),
            'domain': [('vendor_id', '=', self.id), ('company_id', '=', self.env.company.id)],
        }
       
        return action
    
    