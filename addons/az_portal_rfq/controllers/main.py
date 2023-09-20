import json
import logging
from odoo import http, _
from odoo.http import request
import json
from datetime import datetime
from odoo.addons.purchase.controllers.portal import CustomerPortal

_logger = logging.getLogger(__name__)


class CustomerPortal(http.Controller):
    
    
    @http.route("/azk_rfq/portal/save_rfq_price", type='http', auth="user", methods=['post'], website=True )
    def save_rfq_vendor_prices(self, **kw):
        values = {}
        response = None
        line_id = kw.get('order_line_id', False)
        price_unit = kw.get('rfq_unit_price')
        date_planned = kw.get('rfq_date')
        description = kw.get('rfq_description')
        
        if not line_id or not price_unit or not date_planned:
            response = json.dumps({'error': "Error: some fields are required."})
        else:
            rfq_line = request.env['purchase.order.line'].sudo().browse(int(line_id))
            rfq_line.update({'price_unit': price_unit, 'date_planned': datetime.strptime(date_planned, '%Y-%m-%d'), 'vendor_conditions': description})
            rfq = rfq_line.order_id.sudo()

            customerPortal = CustomerPortal()
            response = customerPortal.portal_my_purchase_order(rfq.id, rfq.access_token, **{})
        
        return response
    
    @http.route("/azk_rfq/portal/submit_rfq_price", type='http', auth="user", methods=['post'], website=True, csrf=False)
    def submit_rfq_vendor_prices(self, **kw):
        values = {}
        response = None
        order_id = kw.get('order_id', False)

        if not order_id:
            response = json.dumps({'error': "Error: order id are required."})
        else:
            rfq = request.env['purchase.order'].sudo().browse(int(order_id))
            rfq.update({'qouted': True})
            activity_type = request.env.ref('az_portal_rfq.mail_activity_data_quoted')
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
            customerPortal = CustomerPortal()
            response = customerPortal.portal_my_purchase_order(rfq.id, rfq.access_token, **{})
        
        return response