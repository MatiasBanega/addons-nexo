import json
import logging
from odoo import http, _
from odoo.http import request
from datetime import datetime
from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import pager as portal_pager, get_records_pager

_logger = logging.getLogger(__name__)


class CustomerPortal(portal.CustomerPortal):
    
    @http.route(['/my/proposals', '/my/proposals/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_proposals(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        SaleOrder = request.env['sale.order'].sudo()

        domain = [
            ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
            ('proposal', '=', True)
        ]

        searchbar_sortings = {
            'date': {'label': _('Proposal Date'), 'order': 'date_order desc'},
            'name': {'label': _('Reference'), 'order': 'proposal_name'},
            'stage': {'label': _('Stage'), 'order': 'proposal_stage_id'},
        }

        # default sortby order
        if not sortby:
            sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        proposal_count = SaleOrder.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/proposals",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=proposal_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        proposals = SaleOrder.search(domain, order=sort_order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_proposals_history'] = proposals.ids[:100]

        values.update({
            'date': date_begin,
            'proposals': proposals.sudo(),
            'page_name': 'proposals',
            'pager': pager,
            'default_url': '/my/proposals',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("az_porposal_order.portal_my_proposals", values)
    
    
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id

        SaleOrder = request.env['sale.order'].sudo()
        if 'proposal_count' in counters:
            values['proposal_count'] = SaleOrder.search_count([
                ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
                ('proposal', '=', True)
            ]) if SaleOrder.check_access_rights('read', raise_exception=False) else 0
        

        return values
     

