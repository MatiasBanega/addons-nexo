import logging
from odoo import http, _
from odoo.http import request, Response
from datetime import datetime, timedelta
import odoo
import base64
import json
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from psycopg2.extensions import ISOLATION_LEVEL_READ_COMMITTED
from PIL import Image
from io import BytesIO
import requests
from . import constants
log = logging.getLogger(__name__)



class TokenController(http.Controller):
    
    @http.route('/azk/get_token', methods=['GET', 'POST'], type='http', auth='none', cors='*', csrf=False)
    def get_token(self, **kw):
        """
            Authenticate user and generate access token for him
        """
        try:
            response = None
            result = {
                        'status': constants.STATUS_OK,
                        'message': constants.STATUS_SUCCESS,
                        'payload': '',
                        }
            data = request.get_json_data()
            
            user_name = data.get('username')
            password = data.get('password')
            db_name = odoo.tools.config.get('db_name')
            
            
            if not user_name or not password:
                result['status'] = constants.STATUS_FAIL
                result['message'] = _('Missing username or password')
                
                response =  Response(response=json.dumps(result), status=400)
            else:
                request.session.authenticate(db_name, user_name, password)
                
                uid = request.session.uid
                
                if not uid:
                    result['status'] = constants.STATUS_FAIL
                    result['message'] =  _('Authentication failed')
                    
                    response =  Response(response=json.dumps(result), status=401)
                    log.info("Authentication failed for user %s", user_name)
                else:
                    token_model = request.env['az.api.access.token'].sudo()  
                    token = token_model.create_token(request.env.user)
                    
                    result['status'] = constants.STATUS_SUCCESS
                    result['payload'] =   {
                                            'access_token': token.api_token,
                                        }
                   
                    response =Response(response= json.dumps(result), status=200)
                    
                    log.info("New access token has been generated for user %s", user_name, exc_info=1)
            
        except Exception as e:
            result['status'] = constants.STATUS_FAIL
            result['message'] =  str(e)
           
            response =  Response(json.dumps(result), status=500)
            log.info("Error occurred when trying to generate access token", str(e), exc_info=1)
            
        return response
            
            
    @http.route('/azk/generate_lead', methods=['POST'], type='http', auth='none', cors='*', csrf=False)
    def generate_lead(self, **kw):
        """
            Authenticate user based on access token
            if authenticated, create  lead or return authentication error
        """
        try:
            response = None
            result = {
                        'status': constants.STATUS_OK,
                        'message': constants.STATUS_SUCCESS,
                        'payload': '',
                        }
            token_model = request.env['az.api.access.token'].sudo()
            
            data = request.get_json_data()
            token = data.get('access_token')
            
            token, err_msg = token_model.check_access_token(token)
            
            if not token:
                result['status'] = constants.STATUS_FAIL
                result['message'] =  err_msg
               
                response =  Response(json.dumps(result), status=401)
            else:
                token.update_token_last_accessed()
                request.session.uid = token.user_id.id
                
                user_context = request.env(request.cr, request.session.uid)['res.users'].context_get().copy()
                user_context['uid'] = request.session.uid
                request.session.context.update(user_context)
                request.update_context(**user_context)
                
                cr, uid = request.cr, request.session.uid
                cr._cnx.set_isolation_level(ISOLATION_LEVEL_READ_COMMITTED)
                
                
                lead_model = request.env(cr, uid)['crm.lead']
                
                name = data.get('name', '')
                email = data.get('email', '')
                company = data.get('company', '')
                profile_link = data.get('profile', '')
                website = data.get('website', '')
                phone = data.get('phone', '')
                address = data.get('address', '')
                city_country = data.get('city_country', '')
                
                city, country, country_id = '', False, False
                
                if city_country:
                    city_country_list = city_country.split(',')
                    if len(city_country_list) > 1:
                        city = city_country_list[0].strip()
                        country = city_country_list[-1].strip().lower()
                    else:
                        country = city_country_list[0].strip().lower()
                        
                    if country:
                        country_id = request.env['res.country'].sudo().search([('name', 'ilike', country)], limit=1)
                        if country_id:
                            country_id =  country_id.id  
             
                lead = lead_model.create({
                                            'name': name + _("'s opportunity"),
                                            'contact_name': name,
                                            'email_from': email,
                                            'website': website,
                                            'partner_name': company,
                                            'description': profile_link,
                                            'phone': phone,
                                            'city': city,
                                            'country_id': country_id,
                                            'street': address,
                                            'type': 'lead',
                                        })
                
                data.pop('access_token')
                lead.message_post(body=data)
                    
                result['status'] = constants.STATUS_SUCCESS
                result['payload'] =   {'lead_id': lead.id, 'lead_name': lead.name}
                response = Response(json.dumps(result), status=200)
                
        except Exception as e:
            result['status'] = constants.STATUS_FAIL
            result['message'] = str(e)
            response =  Response(json.dumps(result), status=500)
            log.info("Error occurred when trying to generate lead %s", str(e), exc_info=1)
            
        return response
                
                
                
                
                
                
            
            

        