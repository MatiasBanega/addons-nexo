from odoo import models, fields

class AddDocument(models.TransientModel):
    _name = "add.document.to.mail.composer"
    _description = "Add Document Wizard"
    
    
    def _get_domain_for_document_ids(self):
        """ return domain for the allowed documents to be selected depending on crm workspace structure in settings """
        
        active_model = self.env.context.get("model_name")
        active_id = self.env.context.get("model_id")
        # if the active model is not crm.lead the list view for documents should be empty
        domain = [("id", "=", False)]
        
        if active_model == "crm.lead" and active_id:
            crm_lead_id = self.env["crm.lead"].browse(active_id)
            company_id = crm_lead_id.company_id
            if not company_id:
                selected_company_ids = self._context.get('allowed_company_ids', self.env.company.ids)
                if selected_company_ids and selected_company_ids[0]:
                    company_id = self.env['res.company'].browse(selected_company_ids[0])
                else:
                    company_id = self.env.company
            
            if company_id.documents_crm_settings and company_id.add_attachments_as_document:
                crm_folder = self.env["documents.folder"].search([('is_crm_folder', '=', True)], limit=1)
                if crm_folder:
                    if company_id.crm_workspace_structure == "single_folder":
                        domain = [('folder_id', '=', crm_folder.id)]
                        
                    elif company_id.crm_workspace_structure == "by_customer":
                        if crm_lead_id.partner_id:
                            crm_customer_folder = self.env["documents.folder"].search([('crm_customer_id', '=', crm_lead_id.partner_id.id)])
                            if crm_customer_folder:
                                domain = [('folder_id', '=', crm_customer_folder.id)]
                                
                    elif company_id.crm_workspace_structure == "by_opportunity":
                        crm_lead_folder = self.env["documents.folder"].search([('crm_lead_id', '=', crm_lead_id.id), ('parent_folder_id', '=', crm_folder.id)]).sorted(lambda d: d.id, reverse=True)
                        if crm_lead_folder:
                            domain = [('folder_id', '=', crm_lead_folder[0].id)]
                                
                    elif company_id.crm_workspace_structure == "by_customer_oppurtunity":
                        if crm_lead_id.partner_id:
                            crm_customer_folder = self.env["documents.folder"].search([('crm_customer_id', '=', crm_lead_id.partner_id.id), ('parent_folder_id', '=', crm_folder.id)]).sorted(lambda d: d.id, reverse=True)
                            if crm_customer_folder:
                                crm_lead_folder = self.env["documents.folder"].search([('crm_lead_id', '=', crm_lead_id.id), ('parent_folder_id', '=', crm_customer_folder[0].id)], limit=1)
                                if crm_lead_folder:
                                    domain = [('folder_id', '=', crm_lead_folder.id)]
        
        
        return domain
        
    
    document_ids = fields.Many2many("documents.document", string="Documents", domain=lambda self: self._get_domain_for_document_ids(),)
    
    def add_document_to_mail(self):
        mail_compose_wizard_id = self.env.context.get("mail_compose_message_id", None)
        mail_compose_wizard_id = self.env["mail.compose.message"].browse(mail_compose_wizard_id)
        attachment_ids = self.document_ids.mapped("attachment_id")
        for attach in attachment_ids:
            mail_compose_wizard_id.attachment_ids = [(4, attach.id)]
            
        composer_form_view_id = self.env.ref('mail.email_compose_message_wizard_form').id
        
        return {
                "type": "ir.actions.act_window",
                "view_mode": "form",
                "res_model": "mail.compose.message",
                "res_id": mail_compose_wizard_id.id,
                "view_id": composer_form_view_id,
                "target": "new",
            }
        
    def cancel(self):
        mail_compose_wizard_id = self.env.context.get("mail_compose_message_id", None)
        mail_compose_wizard_id = self.env["mail.compose.message"].browse(mail_compose_wizard_id)
        composer_form_view_id = self.env.ref('mail.email_compose_message_wizard_form').id
        return {
                "type": "ir.actions.act_window",
                "view_mode": "form",
                "res_model": "mail.compose.message",
                "res_id": mail_compose_wizard_id.id,
                "view_id": composer_form_view_id,
                "target": "new",
            }