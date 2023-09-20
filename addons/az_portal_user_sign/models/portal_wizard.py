import re
from odoo import models,_

class PortalWizardUser(models.TransientModel):

    _inherit = 'portal.wizard.user'
    _description = 'Portal User Config'

    # Grant Access & Ask For Vendor Document Sigantaure

    def action_grant_access_vendor(self):
        self.action_grant_access()
        return self.with_context(grant_access="vendor").send_request()
       

    # Grant Access & Ask For Customer Document Sigantaure
    def action_grant_access_customer(self):   
        self.action_grant_access()
        return self.with_context(grant_access="customer").send_request()

    def create_request(self, send=True, without_mail=False):
        action_grant_acces = self.env.context.get('grant_access',[])
        template = None
        if action_grant_acces == "vendor":
            template = self.env.company.supplier_document_sign
        if action_grant_acces == "customer":
            template = self.env.company.customer_document_sign
        signers = [{'partner_id': self.partner_id.id, 'role': False}]
        reference = template.display_name
        subject = _("Signature Request - %(file_name)s", file_name=template.attachment_id.name)
        return self.env['sign.request'].initialize_new(template.id, signers, None, reference, subject, None, send, without_mail)
     

    def send_request(self):
        res = self.create_request()
        request = self.env['sign.request'].browse(res['id'])
        for line in request.request_item_ids:
            line.state = "sent"
        return request.go_to_document()
