import time

from urllib.parse import urlencode, urljoin

from odoo import models, fields, api, _
from odoo.exceptions import Warning, ValidationError


class EmployeeAdvanceSalary(models.Model):
    _inherit = "employee.advance.salary"

    state = fields.Selection(
        selection_add=[
            ("admin", "Admin"),
            ("officer", "Officer"),
            ("qac", "QAC"),
            ("director_1", "Director 1"),
            ("director_2", "Director 2"),
            ("account", "Account"),
            ("confirm",),
        ],
        ondelete={
            "admin": lambda m: m.write({"state": "draft"}),
            "officer": lambda m: m.write({"state": "draft"}),
            "qac": lambda m: m.write({"state": "draft"}),
            "director_1": lambda m: m.write({"state": "draft"}),
            "director_2": lambda m: m.write({"state": "draft"}),
        },
    )
    journal_id = fields.Many2one(
        "account.journal",
        string="Payment Method",
        domain=[("type", "in", ["cash", "bank"])],
    )

    def request_link(self):
        fragment = {}
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        fragment.update(base_url=base_url)
        fragment.update(model=self._name)
        fragment.update(view_type="form")
        fragment.update(id=self.id)
        query = {"db": self.env.cr.dbname}
        res = urljoin(base_url, "?%s#%s" % (urlencode(query), urlencode(fragment)))
        return res

    def get_confirm(self):
        self.state = "admin"
        self.confirm_date = fields.Date.today()
        self.confirm_by_id = self.env.user.id
        url = self.request_link()
        email_from = self.env.user.partner_id.email
        recipients =  "".join(
            self.env.ref("libracycle_process_workflow.group_admin").users.mapped(
                "email"
            )
        )
        mail_template = self.env.ref(
            "lbc_employee_advance_salary.lbc_employee_advance_salary"
        )
        mail_template.with_context(
            {
                "recipient": recipients,
                "url": url,
                "email_from": email_from,
                "title": "Officer",
            }
        ).send_mail(self.id, force_send=False)
        if self.job_id.salary_limit_amount < self.request_amount:
            raise ValidationError(
                _(
                    "You can not request advance salary more than limit amount, please contact your manager."
                )
            )

    def admin_approval(self):
        for rec in self:
            url = self.request_link()
            email_from = self.env.user.partner_id.email
            recipients =  "".join(
                self.env.ref("libracycle_process_workflow.group_officer").users.mapped(
                    "email"
                )
            )
            mail_template = self.env.ref(
                "lbc_employee_advance_salary.lbc_employee_advance_salary"
            )
            mail_template.with_context(
                {
                    "recipient": recipients,
                    "url": url,
                    "email_from": email_from,
                    "title": "Officer",
                }
            ).send_mail(self.id, force_send=False)
            rec.write({"state": "officer"})

    def officer_approval(self):
        for rec in self:
            url = self.request_link()
            email_from = self.env.user.partner_id.email
            recipients =  "".join(
                self.env.ref("libracycle_process_workflow.group_qac").users.mapped(
                    "email"
                )
            )
            mail_template = self.env.ref(
                "lbc_employee_advance_salary.lbc_employee_advance_salary"
            )
            mail_template.with_context(
                {
                    "recipient": recipients,
                    "url": url,
                    "email_from": email_from,
                    "title": "Officer",
                }
            ).send_mail(self.id, force_send=False)
            rec.write({"state": "qac"})

    def qac_approval(self):
        for rec in self:
            url = self.request_link()
            email_from = self.env.user.partner_id.email
            recipients =  "".join(
                self.env.ref(
                    "libracycle_process_workflow.group_director_1"
                ).users.mapped("email")
            )
            mail_template = self.env.ref(
                "lbc_employee_advance_salary.lbc_employee_advance_salary"
            )
            mail_template.with_context(
                {
                    "recipient": recipients,
                    "url": url,
                    "email_from": email_from,
                    "title": "Officer",
                }
            ).send_mail(self.id, force_send=False)
            rec.write({"state": "director_1"})

    def director_1_approval(self):
        for rec in self:
            url = self.request_link()
            email_from = self.env.user.partner_id.email
            recipients =  "".join(
                self.env.ref(
                    "libracycle_process_workflow.group_director_2"
                ).users.mapped("email")
            )
            mail_template = self.env.ref(
                "lbc_employee_advance_salary.lbc_employee_advance_salary"
            )
            mail_template.with_context(
                {
                    "recipient": recipients,
                    "url": url,
                    "email_from": email_from,
                    "title": "Officer",
                }
            ).send_mail(self.id, force_send=False)
            rec.write({"state": "director_2"})

    def director_2_approval(self):
        for rec in self:
            url = self.request_link()
            email_from = self.env.user.partner_id.email
            recipients =  "".join(
                self.env.ref("account.group_account_user").users.mapped("email")
            )
            mail_template = self.env.ref(
                "lbc_employee_advance_salary.lbc_employee_advance_salary"
            )
            mail_template.with_context(
                {
                    "recipient": recipients,
                    "url": url,
                    "email_from": email_from,
                    "title": "Officer",
                }
            ).send_mail(self.id, force_send=False)
            rec.write({"state": "account"})

    def get_apprv_account(self):
        if not self.partner_id or not self.journal_id:
            raise ValidationError(
                _(
                    "Please make sure you have home address set for this employee and also check payment method is selected."
                )
            )
        self.state = "paid"
        self.account_validate_date = fields.Date.today()
        self.account_by_id = self.env.user.id
        payment_methods = self.journal_id.inbound_payment_method_line_ids
        payment_method_id = payment_methods and payment_methods[0] or False
        payment_obj = self.env["account.payment"]
        vals = {
            "partner_id": self.partner_id.id,
            "journal_id": self.journal_id.id,
            "amount": self.request_amount,
            "currency_id": self.currency_id.id,
            "payment_method_line_id": payment_method_id.id
            if payment_method_id
            else False,
            "payment_type": "outbound",
            "partner_type": "supplier",
        }
        pay_id = payment_obj.create(vals)

        res = self.env.ref("account.action_account_payments_payable")
        res = res.sudo().read()[0]
        res["domain"] = str([("id", "in", [pay_id.id])])
        self.payment_id = pay_id.id
        return res

    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("confirm", "Confirmed"),
            ("approved_dept_manager", "Approved by Department"),
            ("approved_hr_manager", "Approved by HR"),
            ("approved_director", "Approved by Director"),
            ("paid", "Paid"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
            ("reject", "Rejected"),
        ],
        string="State",
        readonly=True,
        default="draft",
        track_visibility="onchange",
    )
    partner_id = fields.Many2one("res.partner", string="Employee Partner")
   





class HrJob(models.Model):
    _inherit = "hr.job"

    salary_limit_amount = fields.Float(string="Salary Advance Limit", required=True)
