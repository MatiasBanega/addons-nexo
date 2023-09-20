import json
import logging
import requests
from odoo import http, _
from odoo.http import request, content_disposition, route
import json
from odoo.addons.sale.controllers.portal import CustomerPortal
import base64
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.addons.portal.controllers.mail import _message_post_helper
import unicodedata

_logger = logging.getLogger(__name__)


class CustomerPortalInherited(CustomerPortal):

        
    @http.route(['/my/orders/<int:order_id>/accept/upload_attachment'], type='http', auth='public', methods=['POST'], website=True, csrf=False)
    def azk_portal_quote_accept_upload(self,  order_id, access_token=None, name=None, signature=None, purchase_file=None):
        access_token = access_token or request.httprequest.args.get('access_token')
        try:
            order_sudo = self._document_check_access('sale.order', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return {'error': _('Invalid order.')}
        files = request.httprequest.files.getlist('purchase_file')
        if files:
            file = base64.encodebytes(files[0].read())
            filename = unicodedata.normalize('NFD', files[0].filename)
            result = order_sudo.with_context(mail_create_nosubscribe=True).message_post(body=_('PO Attachment by %s') % (request.env.user.partner_id.name,),
                                             author_id=request.env.user.partner_id.id,
                                             message_type= 'comment',
                                             subtype_xmlid = 'mail.mt_comment',
                                             email_from = request.env.user.partner_id.email,
                                             attachments=[(filename, file)])
        
        return json.dumps({"success": True})
        
        