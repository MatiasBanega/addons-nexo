
from odoo import models, fields, _
import uuid

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    qouted = fields.Boolean('Quoted', track_visibility=True, copy=False)
    submitted_by = fields.Char('Submitted By', copy=False)
    declined = fields.Boolean('Declined', track_visibility=True, copy=False)
    decline_reason_id = fields.Many2one('po.decline.reason', string="PO Decline Reason", copy=False, track_visibility=True)

class PurchaseOrderLine(models.Model):
    _name = 'purchase.order.line'
    _inherit = ['purchase.order.line', 'mail.thread', 'mail.activity.mixin']
    
    vendor_conditions = fields.Char('Vendor Comments', track_visibility=True)
    attached_files = fields.Many2many('ir.attachment', 'sale_line_attach_rel', 'line_id', 'attachment_id', string='Attached File')
  
    
    def write(self, vals):
        res = super().write(vals)
        
        if self.attached_files:
            for file in self.attached_files:
                file.write({'access_token': str(uuid.uuid4())})
                
        return res
    
    
class PODeclineReason (models.Model):
    _name = "po.decline.reason"
    _description = "PO Decline Reason"
    
    po_decline_reason = fields.Text(string="PO Decline Reason", required=True)
    
    def name_get(self):
        res = super().name_get()
        result = []
        ids = []
        for record in res:
            ids.append(record[0])
        
        decs = self.env['po.decline.reason'].sudo().browse(ids)
        
        for record in decs:
            result.append((record.id, record.po_decline_reason))
        
        return result
        