from odoo import models

class MailComposeMessage(models.TransientModel):
    _inherit = "mail.compose.message"
    
    def _action_send_mail(self, auto_commit=False):
        """ to create new RFD or update the state of active RFD in sending email """
        
        if self.model == 'sale.order':
            self = self.with_context(mailing_document_based=True)
            sale_order_id = self.env['sale.order'].browse(self.res_id)
            if sale_order_id:
                if self.env.context.get('az_deliver_files'):
                        sale_order_id.sudo().active_rfd_id.state = 'sent'
                
                if self.env.context.get('az_request_for_delivery'):
                    rfd_id = self.env["request.for.delivery"].sudo().create({"sale_order_id": sale_order_id.id})
                    sale_order_id.sudo().active_rfd_id = rfd_id.id
                    self = self.with_context(az_request_for_delivery=True, az_send_only_partner_ids=self.partner_ids.ids)
        return super(MailComposeMessage, self)._action_send_mail(auto_commit=auto_commit)

class MailFollowe(models.Model):
    _inherit = "mail.followers"
    
    def _get_recipient_data(self, records, message_type, subtype_id, pids=None):
        recipient_data = super()._get_recipient_data(records, message_type, subtype_id, pids)
        if recipient_data and self.env.context.get("az_request_for_delivery") and self.env.context.get('az_send_only_partner_ids'):
            recipient_data = list(filter(lambda a: a[0] in self.env.context.get('az_send_only_partner_ids', []), recipient_data))
        return recipient_data