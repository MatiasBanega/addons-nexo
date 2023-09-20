import json
import logging
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers import portal
from odoo.addons.survey.controllers import main

_logger = logging.getLogger(__name__)


class PortalInherited(portal.CustomerPortal):
    
    @http.route("/sale_order_rfd/reject_rfd", type='http', auth="public", methods=['post'], website=True, csrf=False)
    def az_reject_rfd(self, **kw):
        response = None
       
        if not kw:
            response = json.dumps({'status': 'error', 'msg': 'Something went wrong. No RFD Files Found.'})
        else:
            try:
                for rfd_file_id, rfd_file_comment in kw.items():
                    rfd_file = request.env['request.for.delivery.file'].browse(int(rfd_file_id))
                    if rfd_file and rfd_file_comment:
                        rfd_file.sudo().write({'comment': rfd_file_comment})
            except:
                rfd_file = None
            # to update the state of the RFD one time only reffering to last rfd_file
            if rfd_file:
                delivery_id = rfd_file.delivery_id
                delivery_id.sudo().state = 'rejected'
                
                auth_login_user = None
                if request.env.user.has_group("base.group_public") and request.session.get('auth_login'):
                    auth_login_user = request.env['res.users'].sudo().search([('login', '=', request.session['auth_login'])], limit=1)
                user = auth_login_user or request.env.user
                delivery_id.sudo().sale_order_id.message_post(body=_("The RFD %s has been rejected by %s ", delivery_id.sudo().name, user.name), author_id=user.partner_id.id)
            
            response = json.dumps({'status': 'success', 'msg': 'All RFD Files updated.'})
                
        return response

    @http.route("/sale_order_rfd/approve_rfd", type='http', auth="public", methods=['post'], website=True, csrf=False)
    def az_approve_rfd(self, **kw):
        """ Route called in js used to update the state of RFD and log a message in the SO chatter """
        response = None
        rfd_id = kw.get('rfd_id', None)
        
        if not kw or not rfd_id:
            response = json.dumps({'status': 'error', 'msg': 'Something went wrong. No RFD Found.'})
        else:
            try:
                rfd_id = request.env['request.for.delivery'].browse(int(rfd_id))
            except:
                rfd_id = False
            
            if rfd_id:
                rfd_id.sudo().write({'state': 'approved'})
                
                auth_login_user = None
                if request.env.user.has_group("base.group_public") and request.session.get('auth_login'):
                    auth_login_user = request.env['res.users'].sudo().search([('login', '=', request.session['auth_login'])], limit=1)
                user = auth_login_user or request.env.user
                rfd_id.sale_order_id.sudo().message_post(body=_("The RFD %s has been approved by %s ", rfd_id.sudo().name, user.name), author_id=user.partner_id.id)
             
            response = json.dumps({'status': 'success', 'msg':'Updated RFD state.'})
                 
        return response
    
class Survey(main.Survey):
    
    @http.route('/survey/start/<string:survey_token>', type='http', auth='public', website=True)
    def survey_start(self, survey_token, answer_token=None, email=False, **post):
        """ called on Approve RFD button with customized access_token (passed it in access_token just to use an existing parameter)"""
        
        if email and email.split("-") and email.split("-")[0] == "az_rfd_start_survey":
            
            ctx = dict(request.context)
            try:
                # if the user approving the RFD is public user then take the user from the auth_login if exists
                user = None
                if request.env.user.has_group("base.group_public"):
                    if request.session.get('auth_login'):
                        user = request.env['res.users'].sudo().search([('login', '=', request.session['auth_login'])], limit=1)
                
                user = request.env.user if user is None else user
                
                # adding context to be used on create of the survey answer (survey.user_input) to pass for it specific fields
                ctx.update({'az_rfd_start_survey': True,
                            'rfd_id': int(email.split("-")[1]),
                            'az_rfd_survey_user': user
                           })
            except:
                pass
            request.context = ctx
            
            # settings email back to False
            email = False
        return super().survey_start(survey_token=survey_token, answer_token=answer_token, email=email, **post)
