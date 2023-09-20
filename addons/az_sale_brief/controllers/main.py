import json
import logging
from odoo import http, _
from odoo.http import request
from datetime import datetime
from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import pager as portal_pager, get_records_pager
from odoo.exceptions import UserError, AccessError, MissingError

_logger = logging.getLogger(__name__)


class PortalInherited(portal.CustomerPortal):
    
    @http.route(['/my/briefs', '/my/briefs/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_briefs(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        OrderBrief = request.env['az.brief'].sudo()

        domain = [
            ('partner_id', 'child_of', [partner.commercial_partner_id.id]),
            ('shared', '=', True)
        ]

        searchbar_sortings = {
            'send_date': {'label': _('Brief Date'), 'order': 'send_date'},
            'name': {'label': _('Reference'), 'order': 'name'},
        }

        # default sortby order
        if not sortby:
            sortby = 'send_date'
        sort_order = searchbar_sortings[sortby]['order']

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        brief_count = OrderBrief.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/briefs",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=brief_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        briefs = OrderBrief.search(domain, order=sort_order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_brief_history'] = briefs.ids[:100]

        values.update({
            'date': date_begin,
            'briefs': briefs.sudo(),
            'page_name': 'briefs',
            'pager': pager,
            'default_url': '/my/briefs',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("az_sale_brief.portal_my_briefs", values)
    
    
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id

        OrderBrief = request.env['az.brief'].sudo()
        if 'brief_count' in counters:
            values['brief_count'] = OrderBrief.search_count([
                ('partner_id', 'child_of', [partner.commercial_partner_id.id]),
                ('shared', '=', True)
            ]) if OrderBrief.check_access_rights('read', raise_exception=False) else 0
        

        return values
    
    
    @http.route(['/my/brief'], type='http', auth="user", website=True)
    def my_brief_details(self, id, **kw):
        response = False
        try:
            brief = request.env['az.brief'].sudo().browse(int(id))
            if brief:
                if not request.env.user._is_admin() or brief.partner_id.id != request.env.user.partner_id.id:
                    response = request.redirect('/my')
        except (AccessError, MissingError):
            response = request.redirect('/my')
        
        response = request.render("az_sale_brief.az_brief_details", {'brief': brief, 'page_name': 'brief_details'})
        return response
    
    
    @http.route("/azk_sale_brief/add_reply", type='http', auth="user", methods=['post'], website=True, csrf=False )
    def save_brief_reply(self, **kw):
        values = {}
        response = None
        line_id = kw.get('brief_line_id', False)
        reply = kw.get('reply', False)
       
        if not line_id or not reply:
            response = json.dumps({'status': 'error', 'msg':'some fields are required.'})
        else:
            line = request.env['az.brief.line'].sudo().browse(int(line_id))
            if line.brief_id.partner_id.id != request.env.user.partner_id.id and not request.env.user._is_admin():
                response = json.dumps({'status': 'error', 'msg': "Error: You are not authorized to add reply."})
            else:
                rep = request.env['az.brief.reply'].create({'brief_line_id': line.id, 'reply': reply})
                response = json.dumps({'success': '', 'partner': line.brief_id.partner_id.name, 'reply':rep.reply })
        
        return response
        
    @http.route("/azk_sale_brief/confirm", type='http', auth="user", methods=['post'], website=True, csrf=False )
    def confirm_brief(self, **kw):
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
    
    @http.route("/azk_sale_brief/ask_to_adjust", type='http', auth="user", methods=['post'], website=True, csrf=False )
    def ask_to_adjust_brief(self, **kw):
        values = ctx = {}
        response = None
        brief_id = kw.get('brief_id', False)
       
        if not brief_id:
            response = json.dumps({'status': 'error', 'msg':'missing brief id.'})
        else:
            brief = request.env['az.brief'].sudo().browse(int(brief_id))
            if brief.partner_id.id != request.env.user.partner_id.id and not request.env.user._is_admin():
                response = json.dumps({'error': "Error: You are not authorized to confirm brief."})
            else:
                brief.ask_to_adjust = True
                followers = brief.message_follower_ids.mapped('partner_id').mapped('email')
                adjust_tmpl_template = request.env.ref('az_sale_brief.az_brief_ask_to_adjust')
                so_url = "{0}{1}".format(request.env["ir.config_parameter"].sudo().get_param("web.base.url"), brief.sale_id.get_portal_url())
                brief_url =  brief.get_portal_url()
                ctx['to_mails'] = ",".join(followers)
                ctx['brief_url'] = brief_url
                ctx['so_url'] = so_url
                ctx['brief_name'] = brief.name
                request.env['mail.template'].sudo().browse(adjust_tmpl_template.id).with_context(ctx).send_mail(brief.sale_id.id, force_send=True)
                                                                                      
                brief.sale_id.sudo().message_post(body=_('%s is asking to adjust Brief %s', request.env.user.partner_id.name, brief.name))
                 
                response = json.dumps({'status': 'success', 'msg':''})
                
        return response