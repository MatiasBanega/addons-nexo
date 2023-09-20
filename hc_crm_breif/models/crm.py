# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class Brief(models.Model):
    _inherit = "az.brief"

    crm_id = fields.Many2one('crm.lead', string='CRM')
    sequence = fields.Char('Sequence', required=True, copy=False, readonly=True,  default=lambda self: _('New'))

    state = fields.Selection([('draft', 'Draft'),
                              ('int_approve', 'Internally Approved'),
                              ('cust_approve', 'Customer Approved'),
                              ('behalf_approve', 'Cust-Internal Approved'),
                              ], string='Type', default='draft', readonly=True)

    @api.model
    def create(self, vals):
        # record = super().create(vals)
        # for rec in record:
        print("sds jj", vals)
        if vals.get('sequence', _('New')) == _('New'):
            print("sds jj", vals)
            vals['sequence'] = self.env['ir.sequence'].next_by_code('az.brief.sequence') or _('New')

        return super(Brief, self).create(vals)

    def button_internal_approve(self):
        if self.state == 'draft':
            self.state = 'int_approve'

    def button_cust_approve(self):
        if self.state == 'int_approve':
            self.state = 'cust_approve'

    def button_behalf_cust_approve(self):
        if self.state == 'int_approve':
            self.state = 'behalf_approve'



class CRM(models.Model):
    _inherit = 'crm.lead'



    def open_brief(self):
        sales = self.env['sale.order'].search([('opportunity_id', '=', self.id)])
        breif_ids = self.env['az.brief'].search([('sale_id', 'in', sales.ids)])

        return {
                'name': 'Breif',
                'domain': [('id', 'in', breif_ids.ids)],
                'type': 'ir.actions.act_window',
                # 'view_type': 'list,form',
                'view_mode': 'list,form',
                'res_model': 'az.brief',
            }

    # brief_ids = fields.One2many('az.brief', 'sale_id', string='Briefs', copy=False)
    # active_brief = fields.Many2one('az.brief', string="Active Brief", copy=False)
    # # brief_shared = fields.Boolean(related="active_brief.shared", store=True, string='Shared')
    # # brief_ask_to_adjust = fields.Boolean(related="active_brief.ask_to_adjust", store=True, string='Ask To Adjust')
    #
    # def action_brief(self):
    #     self.ensure_one()
    #     if not self.active_brief:
    #         brief = self.env['az.brief'].create({'name': _('New'), 'crm_id': self.id, 'is_active': True})
    #         brief.base_name = brief.name
    #         self.active_brief = brief
    #         if self.partner_id.id not in brief.message_follower_ids.ids:
    #             brief.message_subscribe(partner_ids=self.partner_id.ids)
    #
    #         # for line in self.order_line:
    #         #     questions = self.env['az.brief.question.definition'].search(
    #         #         [('product_category_id', '=', line.product_id.product_tmpl_id.categ_id.id)])
    #         #     if questions:
    #         #         for q in questions:
    #         #             self.env['az.brief.line'].create({
    #         #                 'brief_id': brief.id,
    #         #                 'sale_line_id': line.id,
    #         #                 'question': q.name,
    #         #                 'answer': q.default_answer,
    #         #                 'portal_bg_color': q.portal_bg_color
    #         #             })
    #
    #     return {
    #         'name': self.active_brief.name,
    #         'type': 'ir.actions.act_window',
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'view_id': self.env.ref('az_sale_brief.brief_form').id,
    #         'res_model': 'az.brief',
    #         'res_id': self.active_brief.id,
    #         'target': 'new'
    #     }