from odoo import models, fields, api
from docutils.nodes import document

class Attachment(models.Model):
    _inherit = "ir.attachment"
    
    @api.model
    def create(self, vals):
        """ to add the attachment as a document in documents app if activated form settings and according
            to the selected structure in the settings.
        """
        res = super().create(vals)
        if res.res_model and res.res_model == 'crm.lead' and res.company_id.documents_crm_settings and res.company_id.add_attachments_as_document:
            res.create_crm_document()
        return res
    
    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if rec.res_model == 'crm.lead' and rec.company_id.documents_crm_settings and rec.company_id.add_attachments_as_document:
                rec.create_crm_document()
        return res
    
    def create_crm_document(self):
        crm_folder_id = self.env["documents.folder"].search([('is_crm_folder','=',True)])
        if crm_folder_id:
            crm_folder_id = crm_folder_id[0]
        else:
            crm_folder_id = self.env["documents.folder"].create({'name' : 'CRM', 'is_crm_folder' : True})
        
        crm_workspace_structure = self.company_id.crm_workspace_structure
        crm_lead_id = self.env["crm.lead"].browse([self.res_id])
        crm_customer_id = self.env["res.partner"].browse([crm_lead_id.partner_id.id]) if crm_lead_id.partner_id else False
        
        document_exists = self.env["documents.document"].search([("attachment_id","=",self.id)])
        if not document_exists:
            if crm_workspace_structure == "single_folder":
                new_document_id = self.env["documents.document"].create({"name": self.name, "type" : self.type, "folder_id" : crm_folder_id.id, "attachment_id": self.id})
            
            elif crm_workspace_structure == "by_customer":
                if crm_customer_id:
                    find_customer_folder = self.env["documents.folder"].search([("crm_customer_id","=",crm_customer_id.id)])
                    if find_customer_folder:
                        customer_folder_id = find_customer_folder[0]
                    else:
                        customer_folder_id = self.env["documents.folder"].create({"name": crm_customer_id.name, "crm_customer_id" : crm_customer_id.id, "parent_folder_id": crm_folder_id.id})
                    
                    new_document_id = self.env["documents.document"].create({"name": self.name, "type" : self.type, "folder_id" : customer_folder_id.id, "attachment_id": self.id})
            
            elif crm_workspace_structure == "by_opportunity":
                find_opportunity_folder = self.env["documents.folder"].search([("crm_lead_id","=",crm_lead_id.id), ("is_subfolder","=",False)])
                if find_opportunity_folder:
                    opp_folder_id = find_opportunity_folder[0]
                else:
                    opp_folder_id = self.env["documents.folder"].create({"name": crm_lead_id.name, "crm_lead_id" : crm_lead_id.id, "parent_folder_id": crm_folder_id.id})
                
                new_document_id = self.env["documents.document"].create({"name": self.name, "type" : self.type, "folder_id" : opp_folder_id.id, "attachment_id": self.id})
            
            elif crm_workspace_structure == "by_customer_oppurtunity":
                if crm_customer_id:
                    find_customer_folder = self.env["documents.folder"].search([("crm_customer_id","=",crm_customer_id.id), ("parent_folder_id","=",crm_folder_id.id)])
                    if find_customer_folder:
                        customer_folder_id = find_customer_folder[0]
                    else:
                        customer_folder_id = self.env["documents.folder"].create({"name": crm_customer_id.name, "crm_customer_id": crm_customer_id.id, "parent_folder_id": crm_folder_id.id})
                    
                    find_crm_folder = self.env["documents.folder"].search([("crm_lead_id","=",crm_lead_id.id), ("parent_folder_id","=",customer_folder_id.id), ("is_subfolder","=",True)])
                    if find_crm_folder:
                        crm_folder_id = find_crm_folder[0]
                    else:
                        crm_folder_id = self.env["documents.folder"].create({"name": crm_lead_id.name, "crm_lead_id" : crm_lead_id.id, "parent_folder_id": customer_folder_id.id, "is_subfolder": True})
                    
                    new_document_id = self.env["documents.document"].create({"name": self.name, "type" : self.type, "folder_id" : crm_folder_id.id, "attachment_id": self.id})