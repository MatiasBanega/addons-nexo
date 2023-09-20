from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError

FIELD_SELECTION = [("required", "Required"), ("optional", "Optional"), ("no", "None")]


class ProjectProjectTask(models.Model):
    _inherit = "project.task"

    
    def get_project_fields(self):
        project_fld_arr = []
        filter = [
            "active",
            "create_date",
            "write_date",
            "write_uid",
            "create_uid",
            "display_name",
            "id",
            "__last_update",
        ]
        fld_type = ["selection", "char", "integer", "float", "date", "datetime"]
        pro_fld = self.env["ir.model.fields"].search(
            [
                ("model", "=", "project.project"),
                ("readonly", "=", False),
                ("name", "not in", filter),
                ("ttype", "in", fld_type),
            ]
        )
        if pro_fld:
            for rec in pro_fld:
                project_fld_arr.append((rec.name, rec.field_description))
        return project_fld_arr

    @api.model
    def default_get(self, flds):
        result = super(ProjectProjectTask, self).default_get(flds)
        if result.get("project_categ_id"):
            proj_cat = self.env["project.project.category"].search([("id", "=", int(result.get("project_categ_id")))])
            if proj_cat:
                if proj_cat:
                    result.update({"type_id": proj_cat.project_type_id.id})
        return result

    def _get_default_employee(self):
        user_id = self.env.uid
        if user_id:
            employee = self.env["hr.employee"].browse(int(user_id))
            return employee.id

    is_category_task = fields.Boolean("Category Task", default=False)

    enable_sales_order_gen = fields.Boolean("Enable Sales Order", default=False)

    project_categ_id = fields.Many2one("project.project.category", "Project Category")

    task_duration_days = fields.Integer(
        "Task Duration",
        default=1,
        help="This is use to specify the number of days to set the deadline after creation of the task.",
    )
    task_escalation_days = fields.Integer(
        "Escalation waiting period",
        default=2,
        help="Escalation will trigger base on the specify day(s) after the task deadline date has trigger",
    )

    task_start_date = fields.Date("Start date")
    task_escalation_trigger = fields.Date("Escalation date")
    task_end_date = fields.Date("End Date")
    # user_id = fields.Many2one(default='')
    escalation_count = fields.Integer("escalation count", default=0)
    department_id = fields.Many2one("hr.department", string="Department")
    task_assign_id = fields.Many2one(
        "hr.employee",
        "Task Assigned to",
        index=True,
        track_visibility="always",
        required=True,
    )
    task_department_id = fields.Many2one(
        "hr.department",
        "Task Department",
        related="task_assign_id.department_id",
        store=True,
    )
    task_supervisor_id = fields.Many2one(
        "hr.employee", "Task Supervisor", related="task_assign_id.coach_id", store=True
    )
    task_manager_id = fields.Many2one(
        "hr.employee",
        "Task Manager",
        related="task_department_id.manager_id",
        store=True,
    )
    require_user_action_flg = fields.Boolean(
        "enable project fields",
        help="If enable task owner will be required to provide the set field before setting task to done ",
    )
    project_fields = fields.Selection(get_project_fields, "Project Field")
    project_fields_type = fields.Char("Project Field Type")
    project_field_string = fields.Char("String Value")
    project_field_date = fields.Date("Date Value")
    project_field_float = fields.Float("Amount Value")
    hide_action_buttons = fields.Boolean("Enable Edit Mode", compute="_compute_edit_mode")

    @api.depends("project_id")
    def _compute_edit_mode(self):
        for rec in self:
            current_user = self.env.user
            team_leader = rec.project_id.user_id
            admin_access = self.env.ref("base.user_root").id
            if current_user == team_leader or current_user.id == admin_access:
                rec.hide_action_buttons = False
            else:
                rec.hide_action_buttons = True

    def toggle_enable_quote_gen(self):
        for record in self:
            record.enable_sales_order_gen = not record.enable_sales_order_gen

    @api.onchange("task_assign_id")
    def on_change_task_assign_id(self):
        if self.task_assign_id:
            user_id = self.task_assign_id.sudo().user_id
            if not user_id:
                raise UserError("%s has no related user on hr settings" % self.task_assign_id.name)
            self.user_id = user_id
        if not self.department_id and self.task_assign_id:
            self.department_id = self.task_department_id

    @api.onchange("project_fields")
    def on_change_project_fields(self):
        if self.project_fields and self.require_user_action_flg:
            fld_rec = self.env["ir.model.fields"].search(
                [("model", "=", "project.project"), ("name", "=", self.project_fields)],
                limit=1,
            )
            if fld_rec:
                self.project_fields_type = fld_rec.ttype

    @api.onchange("project_type_id")
    def on_change_project_type_id(self):
        if self.project_type_id:
            self.type_id = self.project_categ_id.project_type_id

    @api.model
    def create(self, vals):
        # //tracking_disable
        ctx = dict(self._context)
        if vals.get("is_category_task"):
            ctx.update({"tracking_disable": True})
        if vals.get("task_assign_id"):
            if not vals.get("user_id", False):
                task_assign_to_rec = self.env["hr.employee"].browse(int(vals.get("task_assign_id")))
                if not task_assign_to_rec.user_id:
                    raise UserError("%s has no related user assigned on hr settings" % task_assign_to_rec.name)
                vals["user_id"] = task_assign_to_rec.user_id.id
        if vals.get("project_categ_id") and not vals.get("type_id"):
            proj_cat = self.env["project.project.category"].search([("id", "=", int(vals.get("project_categ_id")))])
            if proj_cat:
                vals["type_id"] = proj_cat.project_type_id.id
        return super(ProjectProjectTask, self.with_context(ctx)).create(vals)

    def write(self, vals):
        ctx = dict(self._context)
        check_project_related_field = False

        if vals.get("is_category_task") or self.is_category_task:
            ctx.update({"tracking_disable": True})

        if vals.get("stage_id") and self.require_user_action_flg:
            # check if stage is the end of job workflow
            job_stage = self.env["project.task.type"].search_read(
                [("id", "=", int(vals.get("stage_id")))], ["project_flow"]
            )
            if job_stage:
                if job_stage[0]["project_flow"] == "end":
                    job_string = self.project_field_string or ""
                    job_date = self.project_field_date or ""
                    job_float = self.project_field_float or 0.00
                    if job_string == "" and job_date == "" and job_float <= 0.00:
                        raise UserError("Target Project/Job field value is not provided")
                    check_project_related_field = True
        if (
            self.require_user_action_flg
            and not check_project_related_field
            and (vals.get("project_field_string") or vals.get("project_field_date") or vals.get("project_field_float"))
        ):
            check_project_related_field = True
        if vals.get("project_categ_id") and not vals.get("type_id"):
            proj_cat = self.env["project.project.category"].search([("id", "=", int(vals.get("project_categ_id")))])
            if proj_cat:
                vals["type_id"] = proj_cat.project_type_id.id
        """Reassign Task"""
        task_assigned_to = vals.get("task_assign_id", False)
        if task_assigned_to and not self.user_id:
            task_assign_to_rec = self.env["hr.employee"].sudo().browse(int(task_assigned_to))
            if task_assign_to_rec:
                vals["user_id"] = task_assign_to_rec.user_id.id
            else:
                raise UserError(
                    "%s has no related user assigned. Kindly contact administrator to set related user"
                    % task_assign_to_rec.name
                )
        print("The Context", ctx)
        result = super(ProjectProjectTask, self.with_context(ctx)).write(vals)
        if result:
            if check_project_related_field:
                proj_dict = {}
                proj_fld_type = self.project_fields_type
                if self.project_fields and proj_fld_type:
                    #'selection', 'char', 'integer', 'float', 'date', 'datetime'
                    if proj_fld_type in ["char", "selection"]:
                        proj_dict.update({self.project_fields: self.project_field_string})
                    if proj_fld_type in ["integer", "float"]:
                        amount = self.project_field_float
                        if proj_fld_type == "integer":
                            amount = int(self.project_field_float)
                        proj_dict.update({self.project_fields: amount})
                    if proj_fld_type in ["date", "datetime"]:
                        proj_dict.update({self.project_fields: self.project_field_date})
                if proj_dict:
                    self.project_id.sudo().write(proj_dict)
        return result

    def action_view_item_sales(self):
        self.ensure_one()
        action = self.env.ref("sale.action_quotations")
        project = self.project_id

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
                ("job_id", "=", project.id),
                ("project_id", "=", project.analytic_account_id.id),
            ],
        }

    def create_job_quotation(self):
        for rec in self:
            project_id = rec.project_id
            partner_id = rec.partner_id.id or project_id.partner_id.id
            if not partner_id:
                raise UserError(_("Job has no customer/partner attached"))
            if not rec.enable_sales_order_gen:
                raise UserError("Job quote generation is not enable on this task")
            if not project_id.project_schedule_items_ids:
                raise UserError("Job has no Schedule item, Kindly use Sales order button on the main project")
            if not rec.is_category_task:
                so_quotation = {
                    "partner_id": partner_id,
                    "job_id": project_id.id,
                    "project_id": project_id.analytic_account_id.id,
                    "job_name": project_id.id,  # Check this to ensure it's perfection
                }
                quotation_id = self.env["sale.order"].create(so_quotation)
                if quotation_id:
                    if project_id.project_schedule_items_ids:
                        project_id.project_schedule_items_ids.update({"project_order_id": quotation_id.id})
        return self.action_view_item_sales()

    def _check_task_due(self):
        cur_date = datetime.now().strftime("%Y-%m-%d")
        task_rec = self.env["project.task"].search([("task_escalation_trigger", "<=", cur_date)])
        if task_rec:
            task_rec.escalate_mail()
        return True

    def action_escalate_task(self):
        """
        This function opens a window to compose an email, with the edi sale template message loaded by default
        """
        self.ensure_one()
        ir_model_data = self.env["ir.model.data"]
        try:
            template_id = ir_model_data.get_object_reference("project", "mail_template_data_module_install_project")[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference("mail", "email_compose_message_wizard_form")[1]
        except ValueError:
            compose_form_id = False
        ctx = dict()
        ctx.update(
            {
                "default_model": "project.task",
                "default_res_id": self.ids[0],
                "default_use_template": bool(template_id),
                "default_template_id": template_id,
                "default_composition_mode": "comment",
            }
        )
        return {
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "views": [(compose_form_id, "form")],
            "view_id": compose_form_id,
            "target": "new",
            "context": ctx,
        }

    def escalate_mail(self):
        for task in self:
            if task.stage_id and task.stage_id.project_flow in ["start", "progress"]:
                email_act = task.action_escalate_task()
                if email_act and email_act.get("context"):
                    email_ctx = email_act["context"]
                    email_to = task.user_id.email_formatted or task.user_id.partner_id.email_formatted
                    if task.task_supervisor_id and task.escalation_count <= 2:
                        sup_email = self._get_staff_email(task.task_supervisor_id)
                        email_to = "%s,%s" % (email_to, sup_email)
                    if task.task_manager_id and task.escalation_count > 2:
                        man_email = self._get_staff_email(task.task_supervisor_id)
                        email_to = "%s,%s" % (email_to, man_email)
                    email_ctx.update(
                        default_email_from=task.company_id.email,
                        default_email_to=email_to,
                    )
                    task.with_context(email_ctx).message_post_with_template(email_ctx.get("default_template_id"))
                    cnt = task.escalation_count + 1
                    task.write({"escalation_count": cnt})
        return True

    def _get_staff_email(self, employee_inst):
        if employee_inst:
            User_id = employee_inst.user_id
            if User_id:
                email_add = User_id.email_formatted or User_id.partner_id.email_formatted
                return email_add
        return False


class ProjectTaskType(models.Model):
    _inherit = "project.task.type"

    project_flow = fields.Selection(
        [("start", "Start"), ("progress", "Progress"), ("end", "End")],
        string="Project Process",
        default="progress",
    )
