from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError


class PartnerExtensionRec(models.Model):
    _inherit = "res.partner"

    is_carrier_partner = fields.Boolean("Carrier Company", default=False)


class ProjectPort(models.Model):
    _name = "project.port"

    name = fields.Char("Port Name", required=True)
    address = fields.Text("Port Address")
    port_country_id = fields.Many2one("res.country", "Port country", required=True)
    port_state_id = fields.Many2one(
        "res.country.state",
        "Port state",
        required=True,
        domain="[('country_id', '=', port_country_id)]",
    )


class ProjectTerminal(models.Model):
    _name = "project.terminal"

    name = fields.Char("Terminal Name", required=True)
    address = fields.Text("Terminal Address")
    terminal_country_id = fields.Many2one("res.country", "Terminal country", required=True)
    terminal_state_id = fields.Many2one(
        "res.country.state",
        "Terminal state",
        required=True,
        domain="[('country_id', '=', terminal_country_id)]",
    )


class ProjectScheduleItems(models.Model):
    _name = "project.schedule.items"
    _description = "Project schedule items"

    sequence = fields.Integer("Sequence")
    name = fields.Char("Item Code", required=True)
    project_id = fields.Many2one("project.project", "related project")
    project_type_id = fields.Many2one("project.type", "Project Type", related="project_id.type_id", store=True)
    project_service_means = fields.Selection(related="project_type_id.service_means_type", store=True)
    product_id = fields.Many2one(
        "product.template",
        "Item Type",
        required=True,
        domain="[('is_project_item', '=', True), ('project_type_id', '=', project_type_id)]",
    )
    project_order_id = fields.Many2one("sale.order", "Related sales order")
    description = fields.Char("Item Description", compute="_compute_item_val")
    size = fields.Float(string="Size", required=True)
    product_uom_id = fields.Many2one("uom.uom", "Unit of Measure")
    product_mesured_as = fields.Selection(related="product_uom_id.unit_measured_as", store=True)
    unit = fields.Selection([("ft", "Feet"), ("kg", "Kilogram")], "Unit", default="ft")

    @api.model
    def create(self, vals):
        result = super(ProjectScheduleItems, self).create(vals)
        if result:
            # Get project record
            proj = self.env["project.project"].browse(int(result.project_id.id))
            if proj:
                item_weight = proj.items_total_weight or 0.00
                item_size = proj.items_total_size or 0.00
                item_cnt = proj.schedule_item_count + 1
                product_mesured_as = result.product_mesured_as
                if product_mesured_as == "wgt":
                    item_weight = item_weight + result.size
                else:
                    item_size = item_size + result.size
                proj.write(
                    {
                        "items_total_size": item_size,
                        "items_total_weight": item_weight,
                        "schedule_item_count": item_cnt,
                    }
                )
        return result

    def write(self, vals):
        result = super(ProjectScheduleItems, self).write(vals)
        if result:
            for rec in self:
                proj_schedule = rec.project_id.project_schedule_items_ids
                if proj_schedule:
                    item_cnt = len(proj_schedule)
                    item_weight = 0.00
                    item_size = 0.00
                    for rec in proj_schedule:
                        if rec.product_mesured_as == "wgt":
                            item_weight = item_weight + rec.size
                        else:
                            item_size = item_size + rec.size

                    #
                    rec.project_id.write(
                        {
                            "items_total_size": item_size,
                            "items_total_weight": item_weight,
                            "schedule_item_count": item_cnt,
                        }
                    )
        return result

    @api.depends("size", "product_uom_id")
    def _compute_item_val(self):
        for rec in self:
            if rec.size and rec.product_uom_id:
                rec.description = "%s%s" % (rec.size, rec.product_uom_id.name)
            else:
                rec.description = False

    @api.onchange("product_id", "product_uom_id")
    def onchange_product_id(self):
        if self.product_id:
            # self.lots_visible = self.product_id.tracking != 'none'
            if not self.product_uom_id or self.product_uom_id.category_id != self.product_id.uom_id.category_id:
                self.product_uom_id = self.product_id.uom_id.id
            res = {"domain": {"product_uom_id": [("category_id", "=", self.product_uom_id.category_id.id)]}}
        else:
            res = {"domain": {"product_uom_id": []}}
        return res


class ProjectProject(models.Model):

    _inherit = "project.project"

    description = fields.Html()
    job_allocation_date = fields.Date(
        "Allocation Date",
        required=False,
        tracking=True,
    )
    client_ref = fields.Char(
        "Client Ref.",
        oldname="x_clientref",
        tracking=True,
    )
    job_form_m = fields.Char(
        "Form M./NXP",
        oldname="x_formm",
        tracking=True,
    )
    job_form_m_date = fields.Date(
        "Form M./NXP Collection",
        tracking=True,
    )
    bol_awb_ref = fields.Char(
        "BOL/AWB Number",
        oldname="x_bol_awb",
        tracking=True,
    )
    job_carrier_id = fields.Many2one(
        "res.partner",
        string="Carrier",
        oldname="x_carrier",
        help="Ensure partner carrier flag is enable on partner",
        tracking=True,
    )
    discharge_port_id = fields.Many2one(
        "project.port",
        "Discharge Port",
        required=False,
        tracking=True,
    )
    loading_port_id = fields.Many2one(
        "project.port",
        "Loading Port",
        required=False,
        tracking=True,
    )

    loading_terminal_id = fields.Many2one(
        "stock.location",
        "Loading Terminal",
        tracking=True,
    )
    discharge_terminal_id = fields.Many2one(
        "stock.location",
        "Discharge Terminal",
        required=False,
        tracking=True,
        domain=[("usage", "in", ["transit", "internal"])],
    )
    clearing_agent_id = fields.Many2one("res.partner", string="Clearing Agents", domain=[("supplier", "=", True)])
    vessel_det = fields.Char("Vessel", oldname="x_vessel", tracking=True)
    origin_country_id = fields.Many2one(
        "res.country",
        "Country of origin",
        required=False,
        tracking=True,
    )
    has_job_form_m = fields.Boolean()
    has_bol_awb_ref = fields.Boolean()
    has_arrival_date = fields.Boolean()
    has_job_form_m_date = fields.Date()
    has_job_son = fields.Boolean()
    has_job_liner = fields.Boolean()
    has_job_ba_number = fields.Boolean()
    has_job_cbm = fields.Boolean()
    has_bill_of_lading = fields.Boolean()
    has_shipping_doc = fields.Boolean()
    has_job_paar = fields.Boolean()
    has_job_assessment = fields.Boolean()
    has_job_duty = fields.Boolean()
    has_job_shipping_co = fields.Boolean()
    has_job_terminal_payment = fields.Boolean()
    has_custom_release_date = fields.Boolean()
    has_job_tdo = fields.Boolean()
    has_job_plant_delivery_date = fields.Boolean()
    has_exchange_control_returned = fields.Boolean()
    has_shipping_rating_till = fields.Boolean()
    has_terminal_rating_till = fields.Boolean()
    has_cleared_date = fields.Boolean()
    has_loading_date = fields.Boolean()
    has_delivery_date = fields.Boolean()
    has_container_return_date = fields.Boolean()
    has_total_cycle = fields.Boolean()
    has_job_do = fields.Boolean()
    has_ecd_date = fields.Boolean()
    has_refund_demurrage = fields.Boolean()
    has_cdr = fields.Boolean()
    has_etr = fields.Boolean()
    has_etd = fields.Boolean()
    has_eta = fields.Boolean()
    has_ata = fields.Boolean()
    has_discharge_date = fields.Boolean()
    has_doc_to_agent = fields.Boolean()
    has_rotation_number = fields.Boolean()
    has_nafdac_1_stamp_date = fields.Boolean()
    has_nafdac_2_stamp_date = fields.Boolean()
    has_son_date = fields.Boolean()
    has_pod = fields.Boolean()
    has_free_days = fields.Boolean()
    has_discharge_date = fields.Boolean()
    has_custom_exam_date = fields.Boolean()
    has_fou_release_date = fields.Boolean()
    has_custom_date = fields.Boolean()
    has_gate_release_date = fields.Boolean()
    has_discharge_date = fields.Boolean()
    has_discharge_date = fields.Boolean()



    project_categ_id = fields.Many2one("project.project.category", "Project Category")
    country_of_destination = fields.Many2one(
        "res.country",
        "Destination",
        required=False,
        tracking=True,
    )
    items_count = fields.Integer(compute="_compute_items_count", string="Tasks")
    project_schedule_items_ids = fields.One2many("project.schedule.items", "project_id", "Job Items")
    schedule_item_count = fields.Integer("Counts")
    items_total_weight = fields.Float("Weight", default=0.0)
    items_total_size = fields.Float("Size", default=0.0)
    analysis_balance = fields.Monetary(compute="_compute_project_balance", string="Balance")
    arrival_date = fields.Date(
        "Arrival Date",
        tracking=True,
    )
    job_son = fields.Char(
        "SON",
        tracking=True,
    )
    job_liner = fields.Char(
        "TERMINAL",
        tracking=True,
    )
    job_ba_number = fields.Char(
        "BA Number",
        tracking=True,
    )
    job_cbm = fields.Char(
        "CBM",
        tracking=True,
    )
    bill_of_lading = fields.Date(
        "Bill of lading",
        tracking=True,
    )
    shipping_doc = fields.Date(
        "Shipping Doc",
        tracking=True,
    )
    job_paar = fields.Date(
        "PAAR/NEPZA",
        tracking=True,
    )
    job_assessment = fields.Date(
        "Assessment Notice",
        tracking=True,
    )
    job_duty = fields.Date(
        "Duty Payment Date",
        tracking=True,
    )
    job_shipping_co = fields.Selection(
        [("unpaid", "UNPAID"), ("paid", "PAID")],
        "Shipping Co/Airline",
        default="unpaid",
        tracking=True,
    )
    job_terminal_payment = fields.Selection(
        [("unpaid", "UNPAID"), ("paid", "PAID")],
        "Terminal Payment",
        default="unpaid",
        tracking=True,
    )
    custom_release_date = fields.Date("Custom Release Date", tracking=True)
    job_tdo = fields.Date("TDO", tracking=True)
    job_plant_delivery_date = fields.Date(
        "Plan delivery date",
        tracking=True,
    )
    exchange_control_returned = fields.Date(
        "Exchange control returned",
        tracking=True,
    )

    shipping_rating_till = fields.Date(
        "Shipping Rate Till",
        tracking=True,
    )
    terminal_rating_till = fields.Date(
        "Terminal Rate Till",
        tracking=True,
    )
    cleared_date = fields.Date(
        "Cleared Date",
        tracking=True,
    )
    loading_date = fields.Date(
        "Loading Date",
        tracking=True,
    )
    delivery_date = fields.Date(
        "Delivery Date",
        tracking=True,
    )
    container_return_date = fields.Date(
        "Container Return Date",
        tracking=True,
    )
    total_cycle = fields.Char(
        "Total Cycle",
        compute="_cal_total_cycle",
        store=True,
        default="0",
        tracking=True,
    )
    job_do = fields.Date(
        "DO",
        tracking=True,
    )
    ecd_date = fields.Date(
        "ECD Date",
        tracking=True,
    )
    refund_demurrage_option = fields.Selection(
        [("none", "None"), ("refund", "Refund"), ("demurrage", "Demurrage")],
        "Demurrage/Refund",
        default="none",
        tracking=True,
    )
    refund_demurrage_benef_id = fields.Many2one("res.partner", "R/D Beneficiary", tracking=True)
    refund_demurrage_amount = fields.Float("Amount", tracking=True)

    cdr_beneficiary_id = fields.Many2one("res.partner", "CDR Beneficiary", tracking=True)
    cdr_amount_deposit = fields.Float(
        "Amount Deposited",
        tracking=True,
    )
    cdr_amount_paid = fields.Float(
        "Amount Paid",
        tracking=True,
    )
    cdr_comment = fields.Char(
        "cdr comment",
        tracking=True,
    )

    etr_invoice_number = fields.Char(
        "Invoice Number",
        tracking=True,
    )
    etr_credit_memo = fields.Float(
        "Credit Memo",
        tracking=True,
    )
    etr_amount = fields.Float(
        "Amount",
        tracking=True,
    )

    etd = fields.Date("ETD", tracking=True)
    eta = fields.Date("ETA", tracking=True)
    ata = fields.Date("ATA", tracking=True)
    discharge_date = fields.Date("Discharge Date", tracking=True)
    doc_to_agent = fields.Char("Doc. to agent", tracking=True)
    rotation_number = fields.Char("Rotation Number", tracking=True)
    nafdac_1_stamp_date = fields.Date("NAFDAC 1st stamp date", tracking=True)
    nafdac_2_stamp_date = fields.Date("NAFDAC 2nd stamp sate", tracking=True)
    son_date = fields.Date("SON date", tracking=True)
    pod = fields.Char("POD", tracking=True)
    free_days = fields.Char("No of Free days", tracking=True)
    custom_exam_date = fields.Date("Custom Exams Booking Date", tracking=True)
    custom_date = fields.Date("Custom Exams Date", tracking=True)
    fou_release_date = fields.Date("FOU release Date", tracking=True)
    gate_release_date = fields.Date("Gate release Date", tracking=True)
    empty_container_return_date = fields.Date("Empty Container return Date", tracking=True)
    job_invoiced = fields.Selection(
        [("yes", "YES"), ("no", "NO")],
        "Job Invoiced",
        default="no",
        compute="_check_invoiced_job",
        store=True,
    )

    last_project_comment = fields.Char("Project Comment")

    state = fields.Selection(
        [
            ("new", "New"),
            ("pending", "Pending"),
            ("progress", "In progress"),
            ("deliver", "Delivered"),
            ("cancel", "Cancelled"),
            ("done", "Completed"),
        ],
        "Status",
        default="new",
        tracking=True,
    )

    invoice_nos = fields.Char("Invoice No(s)")
    invoice_amount = fields.Char("Invoice Amount")
    invoice_date = fields.Char("Invoice Date")
    invoice_payment_date = fields.Char("Invoice Payment Date")

    def create(self, vals):
        if vals.get("state"):
            if vals.get("state") == "new":
                vals["state"] = "pending"
        if vals.get("user_id"):
            employee_id = self.env["hr.employee"].sudo().search([("user_id", "=", int(vals.get("user_id")))])
            if not employee_id:
                raise UserError("Project manager has no related user assigned on hr settings")
        return super(ProjectProject, self).create(vals)

    @api.depends("delivery_date", "analytic_account_id.credit")
    def _check_invoiced_job(self):
        for rec in self:
            proj_sales_order = rec.project_sales_order_ids
            if proj_sales_order:
                if any(order.invoice_status in ["invoiced"] for order in proj_sales_order) and rec.delivery_date:
                    rec.job_invoiced = "yes"
                else:
                    rec.job_invoiced = "no"

    # @api.depends("message_ids")
    def _project_message_comment(self):
        pass
        # for rec in self:
        #     if rec.message_ids:
        #         check_for_comment = rec.env["mail.message"].search(
        #             [
        #                 ("model", "=", "project.project"),
        #                 ("res_id", "=", rec.id),
        #                 ("message_type", "=", "comment"),
        #             ],
        #             order="date desc",
        #             limit=1,
        #         )
        #         if check_for_comment:
        #             rec.last_project_comment = check_for_comment.body

    @api.depends("cleared_date", "job_duty")
    def _cal_total_cycle(self):
        for rec in self:
            if rec.cleared_date and rec.job_duty:
                cal_days = rec.cleared_date - rec.job_duty
                if cal_days:
                    rec.total_cycle = "%s day(s)" % cal_days

    @api.onchange("user_id")
    def on_change_task_assign_id(self):
        if self.user_id:
            employee_rec = self.user_id._get_related_employees()
            if not employee_rec:
                raise UserError("%s has no related user on hr settings" % self.user_id.name)

    @api.depends("analytic_account_id.credit", "analytic_account_id.debit")
    def _compute_project_balance(self):
        for rec in self:
            rec.analysis_balance = rec.analytic_account_id.balance
            if abs(rec.analytic_account_id.balance) > 0.0 and (rec.state == "pending" or not rec.state):
                rec.state = "progress"
            else:
                rec.state = "pending"

    def action_view_cost_revenue(self):
        self.ensure_one()
        action = self.env.ref("analytic.action_analytic_account_form")

        return {
            "name": action.name,
            "help": action.help,
            "type": action.type,
            "view_type": action.view_type,
            "view_mode": action.view_mode,
            "target": action.target,
            "context": "{}",
            "res_model": action.res_model,
            "domain": [("id", "=", self.analytic_account_id.id)],
        }

    def import_schedule_item(self):
        """return action to import bank/cash statements. This button should be called only on journals with type =='bank'"""
        action_name = "action_project_schedule_item_import"
        [action] = self.env.ref("project_description.%s" % action_name).read()
        # Note: this drops action['context'], which is a dict stored as a string, which is not easy to update
        action.update({"context": ("{'project_id': " + str(self.id) + "}")})
        return action

    def download_schedule_item_csv(self):
        """return action to import bank/cash statements. This button should be called only on journals with type =='bank'"""
        action_name = "action_project_schedule_item_download"
        [action] = self.env.ref("project_description.%s" % action_name).read()
        # Note: this drops action['context'], which is a dict stored as a string, which is not easy to update
        action.update({"context": ("{'default_project_type_id': " + str(self.type_id.id) + "}")})
        return action

    def _compute_items_count(self):
        for project in self:
            project.items_count = len(project.project_schedule_items_ids)

    def toggle_none(self):
        return False

    def action_pending(self):
        self.write({"state": "pending"})

    def action_progress(self):
        self.write({"state": "progress"})

    def action_done(self):
        self.write({"state": "done"})

    def action_draft(self):
        self.write({"state": "draft"})


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"
    _description = "Analytic Line"

    project_rec_id = fields.Many2one("project.project", "Project")

    @api.model
    def create(self, vals):
        res = super(AccountAnalyticLine, self).create(vals)
        if res:
            if vals.get("account_id"):
                # Get project record and change it state
                proj_acc_id = int(vals.get("account_id"))
                proj_rec = self.env["project.project"].search(
                    [
                        ("state", "=", "pending"),
                        ("analytic_account_id", "=", proj_acc_id),
                    ]
                )
                if proj_rec:
                    proj_rec.action_progress()
        return res
