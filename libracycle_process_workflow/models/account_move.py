from urllib.parse import urlencode, urljoin

from odoo import api, fields, models
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
    _inherit = "account.move"

    state = fields.Selection(
        selection_add=[
            ("qac", "QAC"),
            ("officer", "Officer"), 
            ("approved", "Approved"),
            ("posted",),
        ],
        ondelete={
            "officer": lambda m: m.write({"state": "draft"}),
            "qac": lambda m: m.write({"state": "draft"}),
            "approved": lambda m: m.write({"state": "draft"}),
        },
    )

    bank_account_id = fields.Many2one('res.bank.account', string='Bank Account',  required=False)
    invoice_date = fields.Date(string='Invoice/Bill Date', readonly=False, index=True, copy=False,states={})
    invoice_line_ids = fields.One2many('account.move.line', 'move_id', string='Invoice lines',
        copy=False, readonly=False,
        domain=[('exclude_from_invoice_tab', '=', False)],
        states={})
    line_ids = fields.One2many('account.move.line', 'move_id', string='Journal Items', copy=True, readonly=False,
        states={})

    @api.model_create_multi
    def create(self, vals_list):
        res_ids = super(AccountMove, self).create(vals_list)
        for res_id in res_ids:
            if res_id.move_type in ['in_receipt', 'in_invoice']:
                res_id._send_creation_email_to_qac()
        return res_ids

    def action_post(self):
        res = super(AccountMove,self).action_post()
        if self.move_type == 'in_receipt':
            self.broadcast_notification_qac_done()
        return res

    def _send_creation_email_to_qac(self):
        url = self.request_link()
        email_from = self.env.user.partner_id.email
        recipients = users = "".join(
        self.env.ref("libracycle_process_workflow.group_qac").users.mapped(
                    "email"
                )
            )
        mail_template = self.env.ref(
                "libracycle_process_workflow.mail_template_vendor_create"
            )
        mail_template.with_context(
                {
                    "recipient": recipients,
                    "url": url,
                    "email_from": email_from,
                    "title": self.env.user.name,
                }
            ).send_mail(self.id, force_send=False)


    def action_submit(self):
        for rec in self:
            if rec.partner_id:
                rec.write({"state": "qac"})
                self.broadcast_notification_qac()
            else:
                raise ValidationError("Add a partner to the bill")

    def action_officer_approve(self):
        for rec in self:
            rec.broadcast_notification_account()
            rec.write({"state": "approved"})



    def action_qac_approve(self):
        for rec in self:
            rec.broadcast_notification_officer()
            rec.write({'state': 'officer'})

    def action_reject(self):
        for rec in self:
            rec.write({'state': 'draft'})

    def broadcast_notification_qac(self):
        url = self.request_link()
        email_from = self.env.user.partner_id.email
        recipients = users = "".join(
        self.env.ref("libracycle_process_workflow.group_qac").users.mapped(
                    "email"
                )
            )
        mail_template = self.env.ref(
                "libracycle_process_workflow.libracycle_mail_template_move"
            )
        mail_template.with_context(
                {
                    "recipient": recipients,
                    "url": url,
                    "email_from": email_from,
                    "title": self.env.user.name,
                }
            ).send_mail(self.id, force_send=False)

    def broadcast_notification_officer(self):
        url = self.request_link()
        email_from = self.env.user.partner_id.email
        recipients = users = "".join(
        self.env.ref("libracycle_process_workflow.group_officer").users.mapped(
                    "email"
                )
            )
        mail_template = self.env.ref(
                "libracycle_process_workflow.libracycle_mail_template_move"
            )
        mail_template.with_context(
                {
                    "recipient": recipients,
                    "url": url,
                    "email_from": email_from,
                    "title": self.env.user.name,
                }
            ).send_mail(self.id, force_send=False)


    def broadcast_notification_account(self):
        url = self.request_link()
        email_from = self.env.user.partner_id.email
        recipients = users = "".join(
        self.env.ref("account.group_account_manager").users.mapped(
                    "email"
                )
            )
        mail_template = self.env.ref(
                "libracycle_process_workflow.libracycle_mail_template_move"
            )
        mail_template.with_context(
                {
                    "recipient": recipients,
                    "url": url,
                    "email_from": email_from,
                    "title": self.env.user.name,
                }
            ).send_mail(self.id, force_send=False)

    def broadcast_notification_qac_done(self):
        url = self.request_link()
        email_from = self.env.user.partner_id.email
        recipients = users = "".join(
        self.env.ref("libracycle_process_workflow.group_qac").users.mapped(
                    "email"
                )
            )
        mail_template = self.env.ref(
                "libracycle_process_workflow.mail_template_approved"
            )
        mail_template.with_context(
                {
                    "recipient": recipients,
                    "url": url,
                    "email_from": email_from,
                    "title": self.env.user.name,
                }
            ).send_mail(self.id, force_send=False)


    def request_link(self):
        fragment = {}
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        fragment.update(model=self._name, view_type="form", db=self.env.cr.dbname)
        return urljoin(base_url, "/web?#id=%s&%s" % (self.id, urlencode(fragment)))

 


