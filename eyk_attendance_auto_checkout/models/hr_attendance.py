from odoo import _, api, fields, models
import datetime

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    @api.model
    def auto_checkout(self):
        attendances = self.search([('check_out', '=', False)])
        settings = self.env['res.config.settings'].sudo().get_values()
        auto_checkout_time = float(settings.get('auto_checkout_time', 9))
        auto_send_email = settings.get('auto_send_email', False)
        email_recipient = settings.get('email_recipient', '')

        auto_checkout_seconds = auto_checkout_time * 3600  # Convert hours to seconds
        for attendance in attendances:
            check_in_datetime = fields.Datetime.from_string(attendance.check_in)
            current_datetime = fields.Datetime.now()
            delta = current_datetime - check_in_datetime
            if delta.total_seconds() >= auto_checkout_seconds:
                attendance.check_out = fields.Datetime.now()
                if auto_send_email and email_recipient:
                    employee_name = attendance.employee_id.name
                    subject = _("Automatic Logout from Odoo for %s" % employee_name)
                    message = _("You have been automatically logged out from Odoo after %.2f hours of inactivity.<br> Please remember to check out when you finish work." % auto_checkout_time)
                    mail_dict = {
                                 "subject": subject,
                                 "email_to": email_recipient,
                                 "body_html": message}
                    if mail_dict:
                        mail_create = self.env['mail.mail'].create(mail_dict)
                        mail_create.send()
                
    @api.model
    def run_scheduler(self):
        self.auto_checkout()

class HrAttendanceSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    auto_checkout_time = fields.Float(string='Default Checkout Time', help='Default automatic checkout time in hours', default=9.0)
    auto_send_email = fields.Boolean(string='Automatically Send Email')
    email_recipient = fields.Char(string='Email Recipient', help="Email address to send the report to.")

    def set_values(self):
        super(HrAttendanceSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('eyk_attendance_auto_checkout.auto_checkout_time', str(float(self.auto_checkout_time)))
        self.env['ir.config_parameter'].sudo().set_param('eyk_attendance_auto_checkout.auto_send_email', self.auto_send_email)
        self.env['ir.config_parameter'].sudo().set_param('eyk_attendance_auto_checkout.email_recipient', self.email_recipient)

    @api.model
    def get_values(self):
        res = super(HrAttendanceSettings, self).get_values()
        ir_config = self.env['ir.config_parameter'].sudo()
        res.update(
            auto_checkout_time=float(ir_config.get_param('eyk_attendance_auto_checkout.auto_checkout_time', 9.0)),
            auto_send_email=ir_config.get_param('eyk_attendance_auto_checkout.auto_send_email', False),
            email_recipient=ir_config.get_param('eyk_attendance_auto_checkout.email_recipient', '')
        )
        return res

