import json
import logging
import requests
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
import base64
import unicodedata
import uuid
from odoo.exceptions import  ValidationError

log = logging.getLogger(__name__)


class CustomerPortalInherited(CustomerPortal):

    
    @http.route(['/my/company_documents'], type='http', auth='user',  website=True)
    def azk_portal_company_documents(self,  **kw):
        partner_id = request.env.user.partner_id 
        if partner_id.company_type == 'person' and request.env.user.partner_id.parent_id:
            partner_id = request.env.user.partner_id.parent_id
          
        attachments = request.env['ir.attachment'].sudo().search([('portal', '=', True), ('res_id', '=', partner_id.id)])
       
        response = request.render("az_portal_contact_attachments.portal_contact_documents", {'attachments': attachments, 'page_name': 'company_documents'})
        
        return response
    
    @http.route(['/company_documents/upload'], type='http', auth='user', methods=['POST'], website=True, csrf=False)
    def azk_portal_company_document_upload(self, contact_file, description):
        msg = ""
        status = "success"
        partner_id = request.env.user.partner_id 
        if partner_id.company_type == 'person' and request.env.user.partner_id.parent_id:
            partner_id = request.env.user.partner_id.parent_id
            
        files = request.httprequest.files.getlist('contact_file')
        try:
            if files:
                file = base64.encodebytes(files[0].read())
                filename = unicodedata.normalize('NFD', files[0].filename)
                attachement_values= {
                    'name': filename,
                    'datas': file,
                    'type': 'binary',
                    'description': description,
                    'res_model': 'res.partner',
                    'res_id': partner_id.id,
                    'portal': True,
                    'access_token': str(uuid.uuid4())
                }
                request.env['ir.attachment'].sudo().create(attachement_values)

                result = partner_id.sudo().message_post(body=_('New Porta Attachment by %s:\n%s') % (request.env.user.partner_id.name, filename),

                                                 author_id=partner_id.id,
                                                 message_type= 'comment',
                                                 )
        except Exception as ex:
            log.info("Unable to upload attachment %s", ex)
            msg = str(ex)
            status = "fail"
        
        return json.dumps({"status": status, 'msg': msg})
    
    @http.route(['/company_documents/delete'], type='http', auth='user', methods=['POST'], website=True, csrf=False)
    def azk_portal_company_document_delete(self, attachment_id):
        msg = ""
        status = "success"
        partner_id = request.env.user.partner_id
       
        try:
            request.env['ir.attachment'].sudo().browse(int(attachment_id)).unlink()
        except Exception as ex:
            log.info("Unable to delete attachment %s", ex)
            msg = str(ex)
            status = "fail"
        
        return json.dumps({"status": status, 'msg': msg})
         
        