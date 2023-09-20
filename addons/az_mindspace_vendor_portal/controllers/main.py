import json
import logging
from odoo import http, _
from odoo.http import request
from datetime import datetime
from odoo.addons.purchase.controllers.portal import CustomerPortal



_logger = logging.getLogger(__name__)


class PortalInherited(http.Controller):
    
    
    @http.route("/azk_rfq/portal/save_rfq_price", type='http', auth="user", methods=['post'], website=True )
    def save_rfq_vendor_prices(self, **kw):
        values = {}
        response = None
        line_id = kw.get('order_line_id', False)
        price_unit = kw.get('rfq_unit_price')
#         date_planned = kw.get('rfq_date')
        description = kw.get('rfq_description')
        
        if not line_id or not price_unit:
            response = json.dumps({'error': "Error: some fields are required."})
        else:
            rfq_line = request.env['purchase.order.line'].sudo().browse(int(line_id))
            rfq_line.update({'price_unit': price_unit, 'vendor_conditions': description}) #, 'date_planned': datetime.strptime(date_planned, '%Y-%m-%d')
            rfq = rfq_line.order_id.sudo()

            customerPortal = CustomerPortal()
            response = customerPortal.portal_my_purchase_order(rfq.id, rfq.access_token, **{})
        
        return response
    
    @http.route("/azk_rfq/portal/submit_rfq_price", type='http', auth="user", methods=['post'], website=True, csrf=False)
    def submit_rfq_vendor_prices(self, **kw):
        values = {}
        response = None
        order_id = kw.get('order_id', False)
        submitted_by = kw.get('submitted_by')

        if not order_id:
            response = json.dumps({'error': "Error: order id are required."})
        else:
            rfq = request.env['purchase.order'].sudo().browse(int(order_id))
            rfq.update({'qouted': True, 'submitted_by': submitted_by})
            activity_type = request.env.ref('az_mindspace_vendor_portal.mail_activity_data_quoted')
            rfq_note = '\n'.join(["Product: {0}, Price: {1}, Currnecy: {2}".format(l.product_id.name, l.price_unit, l.order_id.currency_id.name) for l in  rfq.order_line])
           
            request.env['mail.activity'].sudo().create({
                                        'display_name': '',
                                        'summary':'',
                                        'note': rfq_note,
                                        'date_deadline':datetime.now(),
                                        'user_id':rfq.user_id.id,
                                        'res_id':rfq.id,
                                        'res_model_id':request.env['ir.model']._get_id('purchase.order'),
                                        'activity_type_id':activity_type.id})
            rfq.sudo().message_post(body=_(' RFQ submitted by: %s', (submitted_by)))
            customerPortal = CustomerPortal()
            response = customerPortal.portal_my_purchase_order(rfq.id, rfq.access_token, **{})
        
        return response
    
    @http.route("/azk_rfq/portal/terms", type='http', auth="user",  website=True )
    def open_terms_and_conditions(self, **kw):
        terms = request.env.company.x_terms_rfq
        
        return request.render("az_mindspace_vendor_portal.az_vendor_portal_terms", {'terms': terms, 'page_name': 'rfq_terms'})
    
    @http.route("/azk_rfq/portal/decline", type='http', auth="user", methods=['post'], website=True, csrf=False)
    def decline_rfq(self, **kw):
        response = None
        order_id = kw.get('decline_order_line_id', False)
        reason_id = kw.get('po_decline_reson')

        if not order_id:
            response = json.dumps({'status': 'fail','msg': "Error: order id are required."})
        elif not reason_id:
            response = json.dumps({'status': 'fail','msg': "Error: Reason Is Required"})
        else:
            rfq = request.env['purchase.order'].sudo().browse(int(order_id))
            rfq.update({'declined': True, 'decline_reason_id': int(reason_id)})
           
            rfq.sudo().message_post(body=_(' RFQ Declined by: %s', (request.env.user.partner_id.name)))
            response = json.dumps({'status': 'success','msg': ""})
        
        return response
    
