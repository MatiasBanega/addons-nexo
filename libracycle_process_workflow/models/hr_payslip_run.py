from urllib.parse import urlencode, urljoin

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrPayslipRun(models.Model):

    _name = "hr.payslip.run"
    _inherit = ["hr.payslip.run", "mail.thread"]

    state = fields.Selection(
        selection_add=[
            ("qac", "Await QAC"),
            ("officer", "Await Officer"),
            ("account", "Await Account"),
            ("close",),
        ],
        ondelete={
            "officer": lambda m: m.write({"state": "draft"}),
            "qac": lambda m: m.write({"state": "draft"}),

        },
        tracking=True,
    )
    currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', default=lambda self: self.env.user.company_id.currency_id.id)
    payroll_total = fields.Monetary(string="Payroll Total", compute='_compute_total_payroll', currency_field='currency_id')

    def _compute_total_payroll(self):
        for rec in self:
            payslips = self.env['hr.payslip'].search([('payslip_run_id', '=', rec.id)])
            rec.payroll_total = sum([p.net_wage for p in payslips])


    def action_submit_to_officer(self):
        for rec in self:
            url = self.request_link()
            email_from = self.env.user.partner_id.email
            recipients = users = "".join(
                self.env.ref("libracycle_process_workflow.group_qac").users.mapped(
                    "email"
                )
            )
            mail_template = self.env.ref(
                "libracycle_process_workflow.mail_template_payslip_run"
            )
            mail_template.with_context(
                {
                    "recipient": recipients,
                    "url": url,
                    "email_from": email_from,
                    "title": self.env.user.name,
                }
            ).send_mail(self.id, force_send=False)
            rec.write({"state": "officer"})

    def action_submit_to_qac(self):
        for rec in self:
            url = self.request_link()
            email_from = self.env.user.partner_id.email
            recipients = users = "".join(
                self.env.ref("libracycle_process_workflow.group_qac").users.mapped(
                    "email"
                )
            )
            mail_template = self.env.ref(
                "libracycle_process_workflow.mail_template_payslip_run"
            )
            mail_template.with_context(
                {
                    "recipient": recipients,
                    "url": url,
                    "email_from": email_from,
                    "title": self.env.user.name,
                }
            ).send_mail(self.id, force_send=False)
            rec.write({"state": "qac"})

    def action_officer_approved(self):
        for rec in self:
            url = self.request_link()
            email_from = self.env.user.partner_id.email
            recipients = users = "".join(
                self.env.ref(
                    "account.group_account_user"
                ).users.mapped("email")
            )
            mail_template = self.env.ref(
                "libracycle_process_workflow.mail_template_payslip_run"
            )
            mail_template.with_context(
                {
                    "recipient": recipients,
                    "url": url,
                    "email_from": email_from,
                    "title": self.env.user.name,
                }
            ).send_mail(self.id, force_send=False)
            rec.write({"state": "account"})


            
    def action_reject(self):
        for rec in self:
            rec.action_draft()

    def send_notification(self, body, subject, group, email_from):
        partner_ids = []

        users = self.env.ref(group).users
        for user in users:
            partner_ids.append(user.partner_id.id)

        if partner_ids:
            self.message_post(
                body=body,
                email_from=email_from,
                subject=subject,
                partner_ids=partner_ids,
                message_type="email",
                notify_by_email=True,
            )
        return True

    def request_link(self):
        fragment = {}
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        fragment.update(model=self._name, view_type="form", db=self.env.cr.dbname)
        return urljoin(base_url, "/web?#id=%s&%s" % (self.id, urlencode(fragment)))
        