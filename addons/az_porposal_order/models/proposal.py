
from odoo import models, fields, api,  _
import logging


log = logging.getLogger(__name__)

class ProposalStage(models.Model):
    _name = 'az.proposal.stage'

    name = fields.Char('Stage Name', required=True)
    sequence = fields.Integer(default=1)
    is_draft = fields.Boolean('Draft')
    is_pending = fields.Boolean('Pending')
    is_approved = fields.Boolean('Approved')
    is_refused = fields.Boolean('Refused')

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    def _get_default_stage_id(self):
        return self.env['az.proposal.stage'].search([('is_draft', '=', True)], limit=1).id
    
    proposal_name = fields.Char('Proposal Name', required=True, copy=False, readonly=True,  default=lambda self: _('New'))
    proposal = fields.Boolean('Proposal')
    approved = fields.Boolean('Approved', copy=False)
    proposal_stage_id = fields.Many2one('az.proposal.stage', string='Proposal Stage',  default=_get_default_stage_id, copy=False)
    is_proposal_draft = fields.Boolean('Is Proposal Draf', compute="_compute_is_porposal_draft")
    is_proposal_pending = fields.Boolean('Is Proposal Pending', compute="_compute_is_porposal_pending")
    is_proposal_approved = fields.Boolean('Is Proposal Approved', compute="_compute_is_approved_approved")
    is_proposal_refused  = fields.Boolean('Is Proposal Refused', compute="_compute_is_porposal_refused")
    
    def name_get(self):
        res =  super(SaleOrder, self).name_get()
        orders = []
        for rec in res:
            order = self.env['sale.order'].browse(rec[0])
            if order.proposal:
                orders.append((order.id, order.proposal_name))
            else:
                orders.append(rec)
        
        return orders
       
    
    def _compute_is_porposal_draft(self):
        for rec in self:
            rec.is_proposal_draft = True if rec.proposal_stage_id.is_draft else False

    def _compute_is_porposal_pending(self):
        for rec in self:
            rec.is_proposal_pending = True if rec.proposal_stage_id.is_pending else False
            
    def _compute_is_approved_approved(self):
        for rec in self:
            rec.is_proposal_approved = True if rec.proposal_stage_id.is_approved else False
            
    def _compute_is_porposal_refused(self):
        for rec in self:
            rec.is_proposal_refused = True if rec.proposal_stage_id.is_refused else False
            
    @api.model
    def create(self, vals):
        record = super().create(vals)
        for rec in record:
                rec.proposal_name = self.env['ir.sequence'].next_by_code('azk.proposal.order.sequence') or _('New')
        
        return record
    
    def action_convert_to_quotation(self):
        self.ensure_one()
        self.proposal = False
        
    
    def action_ask_for_approval(self):
        self.ensure_one()
        self.proposal_stage_id = self.env['az.proposal.stage'].search([('is_pending', '=', True)], limit=1).id
        activity_type = self.env.ref('az_porposal_order.mail_activity_proposal_approval')
        approval_users = self.env['res.users'].search([('groups_id', '=', self.env.ref("az_porposal_order.group_proposal_approver").id)])
        for user in approval_users:
            self.env['mail.activity'].sudo().create({
                                            'display_name': '',
                                            'summary': _("The proposal %s is pending your approval ") %(self.proposal_name) ,
                                            'user_id': user.id,
                                            'res_id':self.id,
                                            'res_model_id':self.env['ir.model']._get_id('sale.order'),
                                            'activity_type_id':activity_type.id})
    
    def action_proposal_approve(self):
        self.ensure_one()
        self.approved = True
        self.proposal_stage_id = self.env['az.proposal.stage'].search([('is_approved', '=', True)], limit=1).id
        activity_type = self.env.ref('az_porposal_order.mail_activity_proposal_approval')
        approval_users = self.env['res.users'].search([('groups_id', '=', self.env.ref("az_porposal_order.group_proposal_approver").id)])
        act = self.env['mail.activity'].sudo().search([('user_id', 'in', approval_users.mapped('id')), ('activity_type_id', '=', activity_type.id)
                                                       ,('res_id', '=', self.id), ('res_model_id', '=', self.env['ir.model']._get_id('sale.order'))])
        for line in act:
            line.action_done()
            
    def action_proposal_refuse(self):
        self.ensure_one()
        self.proposal_stage_id = self.env['az.proposal.stage'].search([('is_refused', '=', True)], limit=1).id
        activity_type = self.env.ref('az_porposal_order.mail_activity_proposal_approval')
        approval_users = self.env['res.users'].search([('groups_id', '=', self.env.ref("az_porposal_order.group_proposal_approver").id)])
        act = self.env['mail.activity'].sudo().search([('user_id', 'in', approval_users.mapped('id')), ('activity_type_id', '=', activity_type.id)
                                                       ,('res_id', '=', self.id), ('res_model_id', '=', self.env['ir.model']._get_id('sale.order'))])
        for line in act:
            line.action_done()
    
    def action_proposal_send(self):
        ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        self.ensure_one()
        template_id = self.env.ref('az_porposal_order.az_proposal_email_template')
        lang = self.env.context.get('lang')
        template = self.env['mail.template'].browse(template_id.id)
        if template_id.lang:
            lang = template._render_lang(self.ids)[self.id]
        ctx = {
            'default_model': 'sale.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id.id),
            'default_template_id': template_id.id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': False,
            'custom_layout': "mail.mail_notification_paynow",
            'force_email': True,
            'model_description': self.with_context(lang=lang).type_name,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }