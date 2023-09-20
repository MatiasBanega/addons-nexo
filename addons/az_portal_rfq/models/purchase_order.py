
from odoo import models, fields, _
import uuid

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    qouted = fields.Boolean('Quoted', track_visibility=True)


class PurchaseOrderLine(models.Model):
    _name = 'purchase.order.line'
    _inherit = ['purchase.order.line', 'mail.thread', 'mail.activity.mixin']
    
    vendor_conditions = fields.Char('Vendor Conditions', track_visibility=True)
    attached_files = fields.Many2many('ir.attachment', 'sale_line_attach_rel', 'line_id', 'attachment_id', string='Attached File')
    
    
    def write(self, vals):
        res = super().write(vals)
        
        if self.attached_files:
            for file in self.attached_files:
                file.write({'access_token': str(uuid.uuid4())})
                
        return res
        