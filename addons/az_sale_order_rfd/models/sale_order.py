from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    rfd_ids = fields.One2many("request.for.delivery", "sale_order_id", copy=False)
    active_rfd_id = fields.Many2one("request.for.delivery", "Active RFD", copy=False)
    active_rfd_state = fields.Selection(related='active_rfd_id.state')
    rfq_closed = fields.Boolean(default=False)
    client_po = fields.Many2one("ir.attachment", "Client Purchase Order", tracking=True)
    rfd_count = fields.Integer(compute='_compute_rfd_count')
    show_rfd = fields.Boolean(compute='_az_compute_show_buttons')
    show_deliver_files_btn = fields.Boolean(compute='_az_compute_show_buttons')
    
    def _compute_rfd_count(self):
        for record in self:
            record.rfd_count = len(record.rfd_ids.ids)
    
    def _az_compute_show_buttons(self):
        """ Controlling visibility of RFD and Deliver Files Buttons (in xml) using computed fields """
        for record in self:
            record.show_rfd = False
            record.show_deliver_files_btn = False
            
            if record.state == 'sale' and (not record.active_rfd_id or record.active_rfd_id.state == 'rejected'):
                record.show_rfd = True
            
            if record.state == 'sale' and record.active_rfd_id and record.active_rfd_id.state == 'draft' and record.active_rfd_id.high_resolution_link and not record.active_rfd_id.high_resolution_link.isspace():
                record.show_deliver_files_btn = True
            
            
    def request_for_delivery(self):
        """ Open mail Composer wizard to send email to an internal user, to be selected, to fill the documenst in the Active RFD """
        
        self.ensure_one()
        if not self.client_po:
            raise UserError(_('The client purchase order should be uploaded before asking to deliver the designed materials.'))
        
        template_id = self.env.ref('az_sale_order_rfd.sale_order_request_to_upload_delivery_files')
        
        ctx = {
            'default_model': 'sale.order',
            'default_res_id': self.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id.id,
            'default_composition_mode': 'comment',
            'force_email': True,
            'model_description': self.with_context(lang=self.env.context.get('lang')).type_name,
            'az_request_for_delivery': True
        }
        
        return {
            'name': 'RFD',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'res_model': 'mail.compose.message',
            'target': 'new',
            'context': ctx
        }
    
    def deliver_rfd_files(self):
        """ Open a wizard to compose an email to be sent to the SO customer with a button to the SO portal in order 
            to check the attached documents in the active RFD and approve or reject it. """
        
        self.ensure_one()
        if not self.active_rfd_id or not self.active_rfd_id.high_resolution_link:
            raise UserError(_('The High-resolution Link for the active RFD must be filled.'))
        
        template_id = self.env.ref('az_sale_order_rfd.sale_order_rfd_approval_request')
        lang = self.env.context.get('lang')
        if template_id.lang:
            lang = template_id._render_lang(self.ids)[self.id]
        ctx = {
            'default_model': 'sale.order',
            'default_res_id': self.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id.id,
            'default_composition_mode': 'comment',
            'custom_layout': "mail.mail_notification_paynow",
            'force_email': True,
            'model_description': self.with_context(lang=lang).type_name,
            'az_deliver_files': True
        }
        return {
            'name': 'Deliver RFD Files',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }
    
    def action_open_requests_for_delivery(self):
        action = self.env.ref("az_sale_order_rfd.request_for_delivery_action").read()[0]
        action["domain"] = [("sale_order_id", "=", self.id)]
        action["context"] = {'default_sale_order_id': self.id}
        return action
    
    def get_rfd_high_resolution_link(self):
        high_resolution_link = self.active_rfd_id.high_resolution_link
        if high_resolution_link and ('https://' in high_resolution_link or 'http://' in high_resolution_link):
            try:
                high_resolution_link = high_resolution_link.split("https://")[1] or high_resolution_link.split("http://")[1]
            except:
                pass
        
        return high_resolution_link