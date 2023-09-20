import json
import logging
from odoo import http, _
from odoo.http import request
from odoo.addons.purchase.controllers.portal import CustomerPortal

_logger = logging.getLogger(__name__)


class PortalInherited(http.Controller):
    
    @http.route(['/my/vendor_rating'], type='http', auth='user',  website=True)
    def azk_view_vendor_rating(self,  **kw):
        partner_id = request.env.user.partner_id 
        if partner_id.company_type == 'company' and partner_id.parent_id.vendor_rating_ids:
            partner_id = partner_id.parent_id
          
        response = request.render("az_vendor_rating_portal.portal_vendor_rating", {'partner': partner_id, 'page_name': 'vendor_rating'})
        
        return response
    
    
    @http.route("/vendor/portal/get_rating", type='http', auth="user", methods=['get'], website=True )
    def get_vendor_ratings(self, **kw):
        values = {}

        partner_id = request.env.user.partner_id 
        if partner_id.company_type == 'company' and partner_id.parent_id.vendor_rating_ids:
            partner_id = partner_id.parent_id
            
        ratings = list(partner_id.vendor_rating_ids.sorted(key=lambda r: r.rating_element_id.name))
        
        values['labels'] = [ el.rating_element_id.name for el in ratings]
        values['data'] = {'rates': [ round(el.rate * 100, 2) for el in ratings]}
         
        return json.dumps(values)
     

