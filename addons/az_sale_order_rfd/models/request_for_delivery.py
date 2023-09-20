from odoo import models, fields, api, _

class RequestForDelivery(models.Model):
    _name = "request.for.delivery"
    _description = "Request For Delivery"
    
    name = fields.Char(readonly=True)
    sale_order_id = fields.Many2one("sale.order")
    delivery_file_ids = fields.One2many("request.for.delivery.file", "delivery_id")
    state = fields.Selection(selection=[("draft", "Draft"),  ("sent", "Sent"), ("approved", "Approved"), ("rejected", "Rejected")], readonly=True, default="draft")
    high_resolution_link = fields.Char("High-Resolution Link")
    
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('request.for.delivery.sequence')
        return super().create(vals)
    
    def upload_file(self):
        self.ensure_one()
        return {
            'name': _('Upload RFD File'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'context': {
                'active_rfd': self.id,
            },
            'res_model': 'upload.rfd.file.wizard',
            'target': 'new',
        }
    

class RFDFiles(models.Model):
    _name = "request.for.delivery.file"
    _description = "Request For Delivery File"
    
    delivery_id = fields.Many2one("request.for.delivery")
    file_id = fields.Many2one("ir.attachment")
    comment = fields.Char()
    