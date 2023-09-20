import logging
import requests
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal



_logger = logging.getLogger(__name__)


class CustomerPortal(CustomerPortal):
    
    
    @http.route()
    def account(self, **kw):
        self.MANDATORY_BILLING_FIELDS.append('x_studio_trade_license_number')
        self.MANDATORY_BILLING_FIELDS.append('x_studio_trade_license_expiry')
        
        response = super(CustomerPortal, self).account(**kw)
        
        return response
    
    def details_form_validate(self, data):
        self.MANDATORY_BILLING_FIELDS.append('x_studio_trade_license_number')
        self.MANDATORY_BILLING_FIELDS.append('x_studio_trade_license_expiry')
        return super(CustomerPortal, self).details_form_validate(data)
        
        
   