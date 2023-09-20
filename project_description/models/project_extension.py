# © 2016-2017 Elico Corp (https://www.elico-corp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class ProjectProject(models.Model):
    _inherit = "project.project"

    project_sales_order_ids = fields.One2many("sale.order", "job_id", "Job Orders")
    purchase_order_ids = fields.One2many(
        "purchase.order",
        "job_id",
        "Purchase Order",
    )
    purchase_receipt_ids = fields.One2many(
        "account.move",
        "job_id",
        "Purchase Receipts",
    )
    job_invoice_ids = fields.One2many("account.move", "job_id", "Invoice", domain=[("move_type", "=", "out_invoice")])
    job_vendor_bill_ids = fields.One2many(
        "account.move", "job_id", "Vendor Bill", domain=[("move_type", "=", "in_invoice")]
    )
    sales_order_count = fields.Integer(compute="_compute_sales_order_count", string="Sales")
    purchase_order_count = fields.Integer(compute="_compute_purchase_order_count", string="Purchase")
    purchase_order_receipt_count = fields.Integer(
        compute="_compute_purchase_order_receipt_count", string="Purchase Receipt"
    )
    job_invoice_count = fields.Integer(compute="_compute_invoice_count", string="Invoice count")
    job_vendor_bill_count = fields.Integer(compute="_compute_vendor_bill_count", string="Vendor Bill count")

    def _compute_sales_order_count(self):
        for project in self:
            project.sales_order_count = len(project.project_sales_order_ids)

    def _compute_purchase_order_count(self):
        for project in self:
            project.purchase_order_count = len(project.purchase_order_ids)

    def _compute_purchase_order_receipt_count(self):
        for proj in self:
            proj.purchase_order_receipt_count = len(proj.purchase_receipt_ids)

    def _compute_vendor_bill_count(self):
        for proj in self:
            proj.job_vendor_bill_count = len(proj.job_vendor_bill_ids)

    def _compute_invoice_count(self):
        for proj in self:
            proj.job_invoice_count = len(proj.job_invoice_ids)

    def action_view_sales(self):
        self.ensure_one()
        action = self.env.ref("sale.action_quotations")

        return {
            "name": action.name,
            "help": action.help,
            "type": action.type,
            "view_type": action.view_type,
            "view_mode": action.view_mode,
            "target": action.target,
            "context": "{}",
            "res_model": action.res_model,
            "domain": [
                ("job_id", "=", self.id),
                ("project_id", "=", self.analytic_account_id.id),
            ],
        }

    def action_view_purchases(self):
        self.ensure_one()

        action = self.env.ref("purchase.purchase_rfq")
        return {
            "name": action.name,
            "help": action.help,
            "type": action.type,
            "view_type": action.view_type,
            "view_mode": action.view_mode,
            "target": action.target,
            "context": "{}",
            "res_model": action.res_model,
            "domain": [("job_id", "=", self.id)],
        }

    def action_view_vendor_bill(self):
        self.ensure_one()
        action = self.env.ref("account.action_move_in_invoice_type")

        return {
            "name": action.name,
            "help": action.help,
            "type": action.type,
            # "view_type": action.view_type,
            "view_mode": "tree",
            # "view_id": self.env.ref("account.move_supplier_tree").id,
            "target": action.target,
            "context": "{}",
            "res_model": action.res_model,
            "domain": [("job_id", "=", self.id), ("move_type", "=", "in_invoice")],
        }

    def action_view_invoice(self):
        self.ensure_one()
        action = self.env.ref("account.action_move_out_invoice_type")

        return {
            "name": action.name,
            "help": action.help,
            "type": action.type,
            # "view_type": action.view_type,
            "view_mode": "tree",
            # "view_id": self.env.ref("account.move_tree").id,
            "target": action.target,
            "context": "{}",
            "res_model": action.res_model,
            "domain": [("job_id", "=", self.id), ("move_type", "=", "out_invoice")],
        }

    def action_create_invoice(self):

        action = self.env.ref("account.action_move_out_invoice_type")
        context = eval(action.context) or {}
        context.update({"default_job_id": self.id, "default_partner_id": self.partner_id.id})

        return {
            "name": action.name,
            "help": action.help,
            "type": action.type,
            # "view_type": action.view_type,
            "view_mode": "form",
            # "view_id": self.env.ref("account.move_form").id,
            "target": action.target,
            "context": context,
            "res_model": action.res_model,
            "domain": action.domain,
        }

    def action_create_vendor_bill(self):

        action = self.env.ref("account.action_move_in_invoice_type")
        context = eval(action.context) or {}
        context.update({"default_job_id": self.id})

        return {
            "name": action.name,
            "help": action.help,
            "type": action.type,
            # "view_type": action.view_type,
            "view_mode": "form",
            # "view_id": self.env.ref("account.move_supplier_form").id,
            "target": action.target,
            "context": context,
            "res_model": action.res_model,
            "domain": action.domain,
        }

    def action_view_purchases_receipt(self):
        self.ensure_one()
        action = self.env.ref("account_voucher.action_purchase_receipt")

        return {
            "name": action.name,
            "help": action.help,
            "type": action.type,
            "view_type": action.view_type,
            "view_mode": action.view_mode,
            "target": action.target,
            "context": "{}",
            "res_model": action.res_model,
            "domain": [("job_id", "=", self.id)],
        }

    def create_purchases_receipt(self):
        self.ensure_one()
        # account_voucher.action_purchase_receipt_form
        # res = self.env['ir.actions.act_window'].for_xml_id('account_voucher', 'action_purchase_receipt_form')
        action = self.env.ref("account_voucher.action_purchase_receipt")
        context = eval(action.context) or {}
        context.update(
            {
                "default_job_id": self.id,
                "default_analytic_account_id": self.analytic_account_id.id,
                "analytic_account_id": self.analytic_account_id.id,
            }
        )

        return {
            "name": action.name,
            "help": action.help,
            "type": action.type,
            "view_type": action.view_type,
            "view_mode": "form",
            "target": action.target,
            "context": context,
            "res_model": action.res_model,
            "domain": [("job_id", "=", self.id)],
        }

    def action_create_po(self):

        action = self.env.ref("purchase.purchase_rfq")
        context = eval(action.context) or {}
        context.update(
            {
                "default_job_id": self.id,
                "default_analytic_account_id": self.analytic_account_id.id,
                "analytic_account_id": self.analytic_account_id.id,
            }
        )

        return {
            "name": action.name,
            "help": action.help,
            "type": action.type,
            "view_type": action.view_type,
            "view_mode": "form",
            "target": action.target,
            "context": context,
            "res_model": action.res_model,
            "domain": action.domain,
        }

    def create_job_quotation(self):
        for rec in self:
            partner_id = rec.partner_id.id or rec.project_id.partner_id.id
            if not partner_id:
                raise ValidationError(_("Job has no customer/partner attached"))

            so_quotation = {
                "partner_id": partner_id,
                "job_id": rec.id,
                "project_id": rec.analytic_account_id.id,
                "job_name": rec.id,
            }
            quotation_id = self.env["sale.order"].create(so_quotation)
            if quotation_id:
                if rec.project_schedule_items_ids:
                    rec.project_schedule_items_ids.update({"project_order_id": quotation_id.id})
        return self.action_view_sales()
