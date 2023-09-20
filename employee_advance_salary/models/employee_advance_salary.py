import time

# from openerp import models, fields, api, _
# from openerp.exceptions import Warning
from odoo import models, fields, api, _
from odoo.exceptions import Warning, ValidationError


class EmployeeAdvanceSalary(models.Model):
    _name = "employee.advance.salary"
    _description = "Employee Advance Salary"
    # _inherit = ['mail.thread', 'ir.needaction_mixin']
    _inherit = ["mail.thread", "mail.activity.mixin", "portal.mixin"]  #   odoo11
    _order = "id desc"
    _rec_name = "employee_id"

    @api.model
    def get_currency(self):
        return self.env.user.company_id.currency_id

    employee_id = fields.Many2one(
        "hr.employee",
        required=True,
        readonly=True,
        string="Employee",
        states={"draft": [("readonly", False)]},
    )
    request_date = fields.Date(
        string="Request Date",
        default=fields.Date.today(),
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    confirm_date = fields.Date(string="Confirmed Date", readonly=True, copy=False)
    dept_approved_date = fields.Date(
        string="Approved Date(Department)", readonly=True, copy=False
    )
    hr_validate_date = fields.Date(
        string="Approved Date(HR)", readonly=True, copy=False
    )
    director_validate_date = fields.Date(
        string="Approved Date(Director)", readonly=True, copy=False
    )
    account_validate_date = fields.Date(string="Paid Date", readonly=True, copy=False)
    confirm_by_id = fields.Many2one(
        "res.users", string="Confirm By", readonly=True, copy=False
    )
    dept_manager_by_id = fields.Many2one(
        "res.users", string="Department Manager", readonly=True, copy=False
    )
    hr_manager_by_id = fields.Many2one(
        "res.users", string="HR Manager", readonly=True, copy=False
    )
    director_by_id = fields.Many2one(
        "res.users", string="Director", readonly=True, copy=False
    )
    account_by_id = fields.Many2one(
        "res.users", string="Paid By", readonly=True, copy=False
    )

    department_id = fields.Many2one(
        "hr.department",
        string="Department",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    job_id = fields.Many2one(
        "hr.job",
        string="Job Title",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    manager_id = fields.Many2one(
        "hr.employee",
        string="Department Manager",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    request_amount = fields.Float(
        string="Request Amount",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=get_currency,
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    comment = fields.Text(string="Comment")
    user_id = fields.Many2one(
        "res.users",
        default=lambda self: self.env.user,
        string="Request User",
        readonly=True,
    )
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.user.company_id,
        string="Company",
        readonly=True,
    )
    reason_for_advance = fields.Text(
        string="Reason For Advance",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
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
    journal_id = fields.Many2one("account.journal", string="Payment Method")
    payment_id = fields.Many2one("account.payment", string="Payment", readonly=True)

    @api.depends("payment_id", "state")
    def _compute_payed_amount(self):
        for line in self:
            line.paid_amount = line.payment_id.amount

    paid_amount = fields.Float(
        compute=_compute_payed_amount, string="Paid Amount", store=True, readonly=True
    )

    @api.onchange("employee_id", "employee_id.address_home_id")
    def get_department(self):
        for line in self:
            line.department_id = line.employee_id.department_id.id
            line.job_id = line.employee_id.job_id.id
            line.manager_id = line.employee_id.parent_id.id
            line.partner_id = (
                line.employee_id.sudo().address_home_id
                and line.employee_id.sudo().address_home_id.id
                or False
            )


    def request_set(self):
        self.state = "draft"


    def exit_cancel(self):
        self.state = "cancel"


    def get_confirm(self):
        self.state = "confirm"
        self.confirm_date = fields.Date.today()
        self.confirm_by_id = self.env.user.id
        if self.job_id.salary_limit_amount < self.request_amount:
            raise ValidationError(
                _(
                    "You can not request advance salary more than limit amount, please contact your manager."
                )
            )

    
    def get_apprv_dept_manager(self):
        self.state = "approved_dept_manager"
        self.dept_approved_date = fields.Date.today()
        self.dept_manager_by_id = self.env.user.id

    
    def get_apprv_hr_manager(self):
        self.state = "approved_hr_manager"
        self.hr_validate_date = fields.Date.today()
        self.hr_manager_by_id = self.env.user.id

    
    def get_apprv_director(self):
        self.state = "approved_director"
        self.director_validate_date = fields.Date.today()
        self.director_by_id = self.env.user.id

    
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

    
    def get_done(self):
        self.state = "done"

    
    def get_reject(self):
        self.state = "reject"

