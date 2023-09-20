
from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError
import logging
import uuid


_logger = logging.getLogger(__name__)

class BriefQuestionDefinition(models.Model):
    _name = "az.brief.question.definition"
    _description = "Brief Question Definition"
    
    name = fields.Text('Name', required=True)
    default_answer = fields.Html('Default Answer')
    product_category_id = fields.Many2one('product.category', 'Product Category', required=True)
    portal_bg_color = fields.Char('Portal Background Color')
    
class Brief(models.Model):
    _name = "az.brief"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Brief"
    _order = 'name'
    
    name = fields.Char('Name', required=True, copy=False, readonly=True,  default=lambda self: _('New'))
    base_name = fields.Char('Base Name')
    sale_id = fields.Many2one('sale.order', string='Sale Order')
    brief_line_ids = fields.One2many('az.brief.line', 'brief_id', string='Brief Questions')
    is_active = fields.Boolean('Active Brief', default=False)
    shared = fields.Boolean('Shared', copy=False, default=False)
    send_date = fields.Datetime('Sending Date', copy=False)
    revision_number = fields.Integer('Revision Number', copy=False)
    confirmed = fields.Boolean('Confirmed', default=False)
    ask_to_adjust = fields.Boolean('Ask to Adjust', copy=False)
    partner_id = fields.Many2one(related='sale_id.partner_id', store=True, string="Client")
    project_name = fields.Char('Project Name')
    brand  = fields.Char('Brand')
    cs_contact = fields.Many2one('res.partner', string='CS Contact')
    job_number = fields.Char('Job Number')
    first_deadline = fields.Datetime('First Deadline')

    
    def get_portal_url(self):
        self.ensure_one()
        portal_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        portal_link = "%s/my/brief?db=%s&id=%s" % (portal_url, self.env.cr.dbname, self.id)
        
        return portal_link
    
    @api.model
    def create(self, vals):
        record = super().create(vals)
        for rec in record:
            if vals.get('name', _('New')) == _('New'):
                rec.name = self.env['ir.sequence'].next_by_code('az.brief.sequence') or _('New')
            
        return record
    
class BriefLine(models.Model):
    _name = "az.brief.line"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Brief Question"
    _order = 'sequence'
     
    brief_id = fields.Many2one('az.brief', string='Brief')
    sale_line_id = fields.Many2one('sale.order.line', string='Sale Line')
    sale_id = fields.Many2one(related="brief_id.sale_id", store=True)
    question = fields.Char('Question')
    answer = fields.Html('Answer')
    sequence = fields.Integer(default=1)
    attachments = fields.Many2many('ir.attachment', 'brief_line_attach_rel', 'line_id', 'attachment_id', string='Attached Files')
    shared = fields.Boolean('Shared', copy=False, default=False)
    reply_ids = fields.One2many('az.brief.reply', 'brief_line_id', string='Replies')
    reply_count = fields.Integer('Reply Count', compute="_compute_reply_count")
    portal_bg_color = fields.Char('Portal Background Color', default="#bfbfbf")
    
    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if rec.attachments:
                for file in rec.attachments:
                    file.write({'access_token': str(uuid.uuid4())})
        
        return res
        
    @api.depends('reply_ids')
    def _compute_reply_count(self):
        for rec in self:
            rec.reply_count = len(rec.reply_ids)
    
    def action_view_replies(self):
        self.ensure_one()
        return {
            'name': "{0} - Reply".format(self.brief_id.name),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('az_sale_brief.brief_answer_form').id,
            'res_model': 'az.brief.line',
            'res_id': self.id,
            'target': 'new'
        }
        
    def name_get(self):
        res = super().name_get()
        names = []
        for rec in res:
            question = self.env['az.brief.line'].sudo().browse(rec[0]).question
            if question:
                names.append((rec[0], question))
            else:
                names.append(rec)
        
        return names
 
class BriefReply(models.Model):
    _name = "az.brief.reply"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Brief Reply"
    _order = 'sequence'
     
    brief_line_id = fields.Many2one('az.brief.line', string="Brief Question")
    reply = fields.Html('Reply')
    sequence = fields.Integer(default=1)
    
    @api.model
    def create(self, vals):
        records = super().create(vals)
        for rec in records:
            if not rec.brief_line_id.brief_id.is_active:
                raise UserError(_("You can not create reply on inactive brief"))
            followers = rec.sudo().brief_line_id.brief_id.message_follower_ids[0].mapped('partner_id').mapped('email')
            so_url = "{0}{1}".format(self.env["ir.config_parameter"].sudo().get_param("web.base.url"), rec.sudo().brief_line_id.brief_id.sale_id.get_portal_url())
            self.env['mail.mail'].sudo().create({
                        'subject': 'brief reply',
                        'body_html': '%s added a reply on the <a href="%s" target="_blank"> brief  %s</a>' % (self.env.user.partner_id.name, so_url, rec.sudo().brief_line_id.brief_id.name),
                        'email_to':  followers,
                        'email_from': self.env.user.email
                        }).send()
        
        return records
    
    def unlink(self):
        if not self.brief_line_id.brief_id.is_active and not self._context.get('allow_delete'):
            raise UserError(_("You can not create reply on inactive brief"))
        return super().unlink()
     
class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    brief_ids = fields.One2many('az.brief', 'sale_id' , string='Briefs', copy=False)
    active_brief = fields.Many2one('az.brief' , string="Active Brief", copy=False)
    brief_shared = fields.Boolean(related="active_brief.shared", store=True, string='Shared')
    brief_ask_to_adjust = fields.Boolean(related="active_brief.ask_to_adjust", store=True, string='Ask To Adjust')
   
    def action_brief(self):
        self.ensure_one()
        if not self.active_brief:
           brief = self.env['az.brief'].create({'name': _('New'), 'sale_id': self.id, 'is_active': True})
           brief.base_name = brief.name
           self.active_brief = brief
           if self.partner_id.id not in brief.message_follower_ids.ids:
               brief.message_subscribe(partner_ids=self.partner_id.ids)
           
           for line in self.order_line:
               questions  = self.env['az.brief.question.definition'].search([('product_category_id', '=', line.product_id.product_tmpl_id.categ_id.id)])
               if questions:
                   for q in questions:
                       self.env['az.brief.line'].create({
                                                        'brief_id': brief.id,
                                                        'sale_line_id': line.id,
                                                        'question': q.name,
                                                        'answer': q.default_answer,
                                                        'portal_bg_color':  q.portal_bg_color
                                                        })

        
        return {
            'name': self.active_brief.name,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('az_sale_brief.brief_form').id,
            'res_model': 'az.brief',
            'res_id': self.active_brief.id,
            'target': 'new'
        }
        
   
    def action_share_brief(self):
        self.ensure_one()
        template_id = self.env.ref('az_sale_brief.az_brief_email_template')
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
            'mark_brief_as_sent': True,
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
        
    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get('mark_brief_as_sent'):
            self.active_brief.write({'shared': True, 'send_date': datetime.now()})
        return super(SaleOrder, self.with_context(mail_post_autofollow=self.env.context.get('mail_post_autofollow', True))).message_post(**kwargs)

        
    def action_brief_revision(self):
        self.ensure_one()
        if self.active_brief and self.brief_shared:
            brief = self.env['az.brief'].create({'name': self.active_brief.name,
                                                 'base_name': self.active_brief.base_name,
                                                 'sale_id': self.id,
                                                 'is_active': True,
                                                 'project_name':  self.active_brief.project_name,
                                                 'brand':  self.active_brief.brand,
                                                 'cs_contact':  self.active_brief.cs_contact.id,
                                                 'job_number':  self.active_brief.job_number,
                                                 'shared': True,
                                                 'ask_to_adjust': False
                                               })
            for line in self.active_brief.brief_line_ids:
                new_line = self.env['az.brief.line'].create({
                                                                'brief_id': brief.id,
                                                                'sale_line_id': line.sale_line_id.id,
                                                                'question': line.question,
                                                                'answer': line.answer,
                                                                'portal_bg_color':  line.portal_bg_color
                                                            })
                for reply in line.reply_ids:
                    self.env['az.brief.reply'].create({
                                                        'brief_line_id': new_line.id,
                                                        'reply': reply.reply,
            
                                                  })
                    
            brief.is_active = False
            
            self.active_brief.shared = False
            self.active_brief.confirmed = False
            self.active_brief.ask_to_adjust = False
            self.active_brief.revision_number += 1
            self.active_brief.name = "{0}-{1}".format(self.active_brief.base_name, self.active_brief.revision_number)
            for line in self.active_brief.brief_line_ids:
                line.reply_ids.with_context(allow_delete=True).unlink()
            

            self.brief_ids.filtered(lambda b: b.id != self.active_brief.id).write({'is_active': False, 'shared': False})
                
            return {
                'name': self.active_brief.name,
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': self.env.ref('az_sale_brief.brief_form').id,
                'res_model': 'az.brief',
                'res_id': self.active_brief.id,
                'target': 'new'
            }
    
    def action_brief_reassign(self):
        self.ensure_one()
        self.active_brief.ask_to_adjust = False
        reassign_tmpl_template = self.env.ref('az_sale_brief.az_brief_reassign')
        brief_url =  self.active_brief.get_portal_url()
        ctx = {}
        ctx['brief_url'] = brief_url
        ctx['brief_name'] = self.active_brief.name
        self.env['mail.template'].sudo().browse(reassign_tmpl_template.id).with_context(ctx).send_mail(self.id, force_send=True)
                   
        
    def remove_active_brief(self):
        self.ensure_one()
        self.active_brief = False
        
class ProductCategory(models.Model):
    _inherit = 'product.category'
    
    brief_defintion_ids = fields.One2many('az.brief.question.definition', 'product_category_id', string="Brief Questions")
    