from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

from urllib.parse import urljoin, urlencode

STATES = [
    ("draft", "Draft"),
    ("submit", "HOD"),
    ("approved", "Store Officer"),  # Store Officer is a Purchase user
    ("audit", "Internal Audit"),
    ("approval", "Plant Manager"),
    ("approval1", "Store Officer"),
    ("ready", "Ready "),
    ("done", "Done"),
]


class HRDepartment(models.Model):
    """."""

    _inherit = "hr.department"

    location_id = fields.Many2one(comodel_name="stock.location", string="Stock Location")


class IRRequest(models.Model):

    _name = "ng.ir.request"
    _inherit = ["mail.thread"]
    _description = "Internal Requisition"
    _order = "state desc, write_date desc"

    def _current_login_user(self):
        """Return current logined in user."""
        return self.env.uid

    def _current_login_employee(self):
        """Get the employee record related to the current login user."""
        hr_employee = self.env["hr.employee"].search([("user_id", "=", self._current_login_user())], limit=1)
        return hr_employee.id

    name = fields.Char(string="Reference", default="/")
    state = fields.Selection(selection=STATES, default="draft", tracking=True)
    requester = fields.Many2one(comodel_name="res.users", string="User", default=_current_login_user, tracking=True)
    end_user = fields.Many2one(
        comodel_name="hr.employee", string="Employee", default=_current_login_employee, required=True
    )
    request_date = fields.Date(
        string="Request Date", default=lambda self: fields.Date.today(), help="The day in which request was initiated"
    )
    request_deadline = fields.Date(string="Deadline")
    hod = fields.Many2one(comodel_name="hr.employee", related="end_user.parent_id", string="Manager")
    department = fields.Many2one(comodel_name="hr.department", related="end_user.department_id", string="Department")
    request_type = fields.Selection(
        selection=[("purchase", "Purchase"), ("sale", "Sale")], string="Request Type", required=True
    )
    dst_location_id = fields.Many2one(
        comodel_name="stock.location", string="Destination Location", help="Departmental Stock Location", tracking=True,
    )
    src_location_id = fields.Many2one(
        comodel_name="stock.location", string="Source Location", help="Departmental Stock Location", tracking=True,
    )
    approve_request_ids = fields.One2many(
        comodel_name="ng.ir.request.approve", inverse_name="request_id", string="Request Line", required=True
    )
    reason = fields.Text(string="Rejection Reason")
    availaibility = fields.Boolean(string="Availaibility", compute="_compute_availabilty")
    warehouse_id = fields.Many2one(comodel_name="stock.warehouse", string="Warehouse")
    company_id = fields.Many2one(
        "res.company",
        "Company",
        default=lambda self: self.env["res.company"]._company_default_get(),
        index=True,
        required=True,
    )

    @api.depends("approve_request_ids")
    def _compute_availabilty(self):
        count_total = len(self.approve_request_ids)
        count_avail = len([appr_id.state for appr_id in self.approve_request_ids if appr_id.state == "available"])
        self.availaibility = count_total == count_avail

    @api.onchange("hod")
    def _onchange_hod(self):
        if self.department:
            self.dst_location_id = self.department.location_id

    @api.model
    def create(self, vals):
        seq = self.env["ir.sequence"].next_by_code("ng.ir.request")
        vals.update(name=seq)
        res = super(IRRequest, self).create(vals)
        return res

    def submit(self):
        if not self.approve_request_ids:
            raise UserError("You can not submit an empty item list for requisition.")
        else:
            # fetch email template.
            recipient = self.recipient("hod", self.hod)
            url = self.request_link()
            mail_template = self.env.ref("ng_internal_requisition.ng_internal_requisition_submit")
            mail_template.with_context({"recipient": recipient, "url": url}).send_mail(self.id, force_send=False)
            self.write({"state": "submit"})

    def department_manager_approve(self):
        context = self.env.context
        if self:
            approved = context.get("approved")
            if not approved:
                # send rejection mail to the author.
                return {
                    "type": "ir.actions.act_window",
                    "res_model": "ir.request.wizard",
                    "views": [[False, "form"]],
                    "context": {"request_id": self.id},
                    "target": "new",
                }
            else:
                # move to next level and send mail
                url = self.request_link()
                recipient = self.recipient("department_manager", self.department)
                mail_template = self.env.ref("ng_internal_requisition.ng_internal_requisition_approval")
                mail_template.with_context({"recipient": recipient, "url": url}).send_mail(self.id, force_send=False)
                self.write({"state": "approved"})

    def store_officer_approve(self):
        context = self.env.context
        approved = context.get("approved")
        if not approved:
            # send mail to the author.
            return {
                "type": "ir.actions.act_window",
                "res_model": "ir.request.wizard",
                "views": [[False, "form"]],
                "context": {"request_id": self.id},
                "target": "new",
            }
        else:
            not_available = self.approve_request_ids.filtered(lambda r: r.state not in ["available", "awaiting"])
            if not_available:
                raise UserError("All items must be availaible before you can approve this record")
            else:
                # move to next level and send mail
                self.write({"state": "audit"})

    def warehouse_officer_confirm(self):
        context = self.env.context
        if not self.approve_request_ids:
            raise UserError("Please add requested items.")
        else:
            url = self.request_link()
            recipient = self.recipient("department_manager", self.department)
            mail_template = self.env.ref("ng_internal_requisition.ng_internal_requisition_warehouse_officer")
            mail_template.with_context({"recipient": recipient, "url": url}).send_mail(self.id, force_send=False)
            self.write({"state": "approval"})

    def check_quantity_available(self):
        """"""
        for rec in self:
            for line in rec.approve_request_ids:
                line._compute_quantity_available()

    def internal_confirmation(self):
        context = self.env.context
        approved = context.get("approved")
        if not approved:
            return {
                "type": "ir.actions.act_window",
                "res_model": "ir.request.wizard",
                "views": [[False, "form"]],
                "context": {"request_id": self.id},
                "target": "new",
            }
        else:
            # move to next level and send mail
            self.write({"state": "approval"})

    def action_do_transfer(self):
        if self:
            src_location_id = self.src_location_id.id
            dst_location_id = self.dst_location_id.id
            domain = [
                ("code", "=", "internal"),
                ("active", "=", True),
                ("default_location_src_id", "=", self.src_location_id.id),
            ]
            stock_picking = self.env["stock.picking"]
            picking_type = self.env["stock.picking.type"].search(domain, limit=1)
            payload = {
                "location_id": src_location_id,
                "location_dest_id": dst_location_id,
                "picking_type_id": picking_type.id,
            }
            stock_picking_id = stock_picking.create(payload)
            move_id = self.stock_move(self.approve_request_ids, stock_picking_id)
            self.process(stock_picking_id)

    def stock_move(self, request_ids, picking_id):
        """."""
        stock_move = self.env["stock.move"]
        for request_id in request_ids:
            payload = {
                "product_id": request_id.product_id.id,
                "name": request_id.product_id.display_name,
                "product_uom_qty": request_id.quantity,
                "product_uom": request_id.uom.id,
                "picking_id": picking_id.id,
                "location_id": picking_id.location_id.id,
                "location_dest_id": picking_id.location_dest_id.id,
            }

            stock_move.create(payload)
            print(payload)
            print(request_id.state)
            request_id.write({"transferred": True})
        self.write({"state": "done"})

    def process(self, picking_id):
        pickings_to_do = self.env["stock.picking"]
        pickings_not_to_do = self.env["stock.picking"]

        for picking in picking_id:
            # If still in draft => confirm and assign
            if picking.state == "draft":
                picking.action_confirm()
                if picking.state != "assigned":
                    picking.action_assign()
                    if picking.state != "assigned":
                        raise UserError(
                            _(
                                "Could not reserve all requested products. Please use the 'Mark as Todo' button to handle the reservation manually."
                            )
                        )
            for move in picking.move_lines.filtered(lambda m: m.state not in ["done", "cancel"]):
                for move_line in move.move_line_ids:
                    move_line.qty_done = move_line.product_uom_qty

        pickings_to_validate = picking_id.ids
        if pickings_to_validate:
            pickings_to_validate = self.env["stock.picking"].browse(pickings_to_validate)
            pickings_to_validate = pickings_to_validate - pickings_not_to_do
            pickings_to_validate.action_confirm()
            return pickings_to_validate.with_context(skip_immediate=True).button_validate()
        return True

    def recipient(self, recipient, model):
        """Return recipient email address."""
        if recipient == "hod":
            workmails = model.address_id, model.work_email
            workmail = {workmail for workmail in workmails if workmail}
            workmail = workmail.pop() if workmail else model.work_email
            if not isinstance(workmail, str):
                try:
                    return workmail.email
                except:
                    pass
            return workmail
        elif recipient == "department_manager":
            manager = model.manager_id
            return manager.work_email or manager.address_id.email

    def request_link(self):
        fragment = {}
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        model_data = self.env["ir.model.data"]
        fragment.update(base_url=base_url)
        fragment.update(model="ng.ir.request")
        fragment.update(view_type="form")
        fragment.update(
            action=model_data.get_object_reference("ng_internal_requisition", "ng_internal_requisition_action_window")[
                -1
            ]
        )
        fragment.update(id=self.id)
        query = {"db": self.env.cr.dbname}
        res = urljoin(base_url, "?%s#%s" % (urlencode(query), urlencode(fragment)))
        return res

    def plant_manager_approve(self):
        for rec in self:
            context = self.env.context
            approved = context.get("approved")
            if not approved:
                return {
                    "type": "ir.actions.act_window",
                    "res_model": "ir.request.wizard",
                    "views": [[False, "form"]],
                    "context": {"request_id": self.id},
                    "target": "new",
                }
            else:
                # move to next level and send mail
                self.write({"state": "ready"})

    def accept_requisition(self):
        for rec in self:
            rec.action_do_transfer()
            # rec.write({'state': 'transfer'})
