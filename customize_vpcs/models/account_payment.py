from odoo import models, fields, api, _
from datetime import datetime, date
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    validate_payment_date = fields.Date(string='Payment Validate Date')
    analytic_account_id = fields.Many2one('account.analytic.account')

    def write(self, vals):
        data = super(AccountPayment, self).write(vals)
        get_department_id = self.env['hr.department'].search([('name', '=', 'QAC')])
        get_employee_id = self.env['hr.employee'].search([('department_id', '=', get_department_id.id)])
        if vals:
            data = 'record id=%s changed.\n\n' % (self.id)
            for key in vals:
                data += '%s --> %s \n\n,' % (key, vals[key])
            for emp in get_employee_id:
                send_message = emp.message_post(body=data)
        return data

    @api.constrains('date')
    def _check_payment_date(self):
        for rec in self:
            if rec.date < date.today():
                raise ValidationError('Please enter a valid date for payment')

    def action_post(self):
        res = super(AccountPayment, self).action_post()
        self.update({
            'validate_payment_date': date.today(),
        })

        return res
