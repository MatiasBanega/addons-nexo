from odoo import _, api, fields, models
from urllib.parse import urlencode, urljoin

class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    state = fields.Selection(
        selection_add=[("hod", "HOD"), ("final", "Final Approval"), ("approve",)],
        ondelete={
            "hod": lambda m: m.write({"state": "approve"}),
            "final": lambda m: m.write({"state": "approve"}),
        },
    )

    def request_link(self):
        fragment = {}
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        fragment.update(model=self._name, view_type="form", db=self.env.cr.dbname)
        return urljoin(base_url, "/web?#id=%s&%s" % (self.id, urlencode(fragment)))

    def approve_expense_hod_sheets(self):
        for rec in self:
            url = self.request_link()
            email_from = self.env.user.partner_id.email
            recipients = "".join(
                self.env.ref(
                    "libracycle_process_workflow.group_hr_expense_hod_approver"
                ).users.mapped("email")
            )
            mail_template = self.env.ref(
                "libracycle_process_workflow.mail_template_expense_sheet"
            )
            mail_template.with_context(
                {
                    "recipient": recipients,
                    "url": url,
                    "email_from": email_from,
                }
            ).send_mail(self.id, force_send=False)
            rec.write({"state": "final"})

    def approve_expense_final_sheets(self):
        for rec in self:
            url = self.request_link()
            email_from = self.env.user.partner_id.email
            recipients = "".join(
                self.env.ref(
                    "libracycle_process_workflow.group_hr_expense_hod_approver"
                ).users.mapped("email")
            )
            mail_template = self.env.ref(
                "libracycle_process_workflow.mail_template_expense_sheet"
            )
            mail_template.with_context(
                {
                    "recipient": recipients,
                    "url": url,
                    "email_from": email_from,
                }
            ).send_mail(self.id, force_send=False)
            rec.write({"state": "approve"})

    @api.depends_context("uid")
    @api.depends("employee_id")
    def _compute_can_approve(self):
        is_approver = self.user_has_groups(
            "hr_expense.group_hr_expense_team_approver, hr_expense.group_hr_expense_user, libracycle_process_workflow.group_hr_expense_hod_approver, libracycle_process_workflow.group_hr_expense_final_approver"
        )
        is_manager = self.user_has_groups("hr_expense.group_hr_expense_manager")
        for sheet in self:
            sheet.can_approve = is_manager or (
                is_approver and sheet.employee_id.user_id != self.env.user
            )

    def _do_approve(self):
        self._check_can_approve()

        notification = {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("There are no expense reports to approve."),
                "type": "warning",
                "sticky": False,  # True/False will display for few seconds if false
            },
        }

        filtered_sheet = self.filtered(lambda s: s.state in ["submit", "draft"])
        if not filtered_sheet:
            return notification
        for sheet in filtered_sheet:
            sheet.write(
                {"state": "hod", "user_id": sheet.user_id.id or self.env.user.id}
            )
        notification["params"].update(
            {
                "title": _("The expense reports were successfully approved."),
                "type": "success",
                "next": {"type": "ir.actions.act_window_close"},
            }
        )

        self.activity_update()
        return notification
