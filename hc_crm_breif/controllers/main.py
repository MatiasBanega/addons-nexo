import json
import logging
from odoo import http, _
from odoo.http import request
from datetime import datetime
from odoo.addons.az_sale_brief.controllers import main
from odoo.addons.portal.controllers.portal import pager as portal_pager, get_records_pager
from odoo.exceptions import UserError, AccessError, MissingError

_logger = logging.getLogger(__name__)


class BriefInherited(main.PortalInherited):
    

    @http.route("/azk_sale_brief/confirm", type='http', auth="user", methods=['post'], website=True, csrf=False )
    def confirm_brief(self, **kw):
        print("dfjhsdkjfhskdjhfjksdhfj 222")
        values = ctx = {}
        response = None
        brief_id = kw.get('brief_id', False)
       
        if not brief_id:
            response = json.dumps({'status': 'error', 'msg':'missing brief id.'})
        else:
            brief = request.env['az.brief'].sudo().browse(int(brief_id))
            if brief.partner_id.id != request.env.user.partner_id.id and not request.env.user._is_admin():
                response = json.dumps({'status': 'error', 'msg': "Error: You are not authorized to confirm brief."})
            else:
                brief.confirmed = True
                brief.state = 'cust_approve'
                followers = brief.message_follower_ids[0].mapped('partner_id').mapped('email')
                so_url = "{0}{1}".format(request.env["ir.config_parameter"].sudo().get_param("web.base.url"), brief.sale_id.get_portal_url())
                brief_url =  brief.get_portal_url()
                confirm_tmpl_template = request.env.ref('az_sale_brief.az_brief_confirm')
                ctx['to_mails'] = ",".join(followers)
                ctx['brief_url'] = brief_url
                ctx['so_url'] = so_url
                ctx['brief_name'] = brief.name
                request.env['mail.template'].sudo().browse(confirm_tmpl_template.id).with_context(ctx).send_mail(brief.sale_id.id, force_send=True)
                
                brief.sale_id.sudo().message_post(body=_('Brief %s has been confirmed by %s', brief.name, request.env.user.partner_id.name))
                response = json.dumps({'status': 'success', 'msg':''})
                
        return response
    
