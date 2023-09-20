# © 2016-2017 Elico Corp (https://www.elico-corp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError

FIELD_SELECTION = [("required", "Required"), ("optional", "Optional"), ("no", "None")]


class ProjectProjectCategory(models.Model):
    _name = "project.project.category"

    name = fields.Char("Name", required=True, translate=True, select=True)
    description = fields.Char("Description", translate=True)
    active = fields.Boolean("Active", default=True)
    project_type_id = fields.Many2one("project.type", "Project Type", required=False)
    default_task_count = fields.Integer(compute="_compute_default_task_count", string="Default Tasks")
    task_count = fields.Integer(compute="_compute_task_count", string="Tasks")

    task_needaction_count = fields.Integer(compute="_compute_task_needaction_count", string="Tasks")
    project_category_task_ids = fields.One2many("project.task", "project_categ_id", string="Project Default Tasks")
    default_stage_ids = fields.Many2many("project.task.type", string="Default Stages")

    has_job_form_m = fields.Selection(
        FIELD_SELECTION,
        "Form M.",
        required=True,
        default="no",
        help="Display Form M. on project",
    )
    has_job_form_m_date = fields.Selection(
        FIELD_SELECTION,
        "Form M. Date",
        required=True,
        default="no",
        help="Display Form M. Date on project",
    )
    has_bol_awb_ref = fields.Selection(
        FIELD_SELECTION,
        "BOL/AWB Ref",
        required=True,
        default="optional",
        help="Display BOL/AWB Ref on project",
    )

    has_arrival_date = fields.Selection(
        FIELD_SELECTION,
        "Arrival Date",
        required=True,
        default="no",
        help="Display arrival date on project",
    )
    has_job_son = fields.Selection(
        FIELD_SELECTION,
        "SON",
        required=True,
        default="no",
        help="Display SON field on project",
    )
    has_job_liner = fields.Selection(
        FIELD_SELECTION,
        "LINER",
        required=True,
        default="no",
        help="Display LINER field on project",
    )
    has_job_ba_number = fields.Selection(
        FIELD_SELECTION,
        "BA Number",
        required=True,
        default="no",
        help="Display BA Number field on project",
    )
    has_job_cbm = fields.Selection(
        FIELD_SELECTION,
        "CBM",
        required=True,
        default="no",
        help="Display CBM field on project",
    )
    has_bill_of_lading = fields.Selection(
        FIELD_SELECTION,
        "Bill of Lading",
        required=True,
        default="no",
        help="Display Bill of Lading field on project",
    )
    has_shipping_doc = fields.Selection(
        FIELD_SELECTION,
        "Shipping Doc",
        required=True,
        default="no",
        help="Display Shipping Doc field on project",
    )
    has_job_paar = fields.Selection(
        FIELD_SELECTION,
        "PAAR",
        required=True,
        default="no",
        help="Display PAAR field on project",
    )
    has_job_assessment = fields.Selection(
        FIELD_SELECTION,
        "Assessment",
        required=True,
        default="no",
        help="Display Assessment field on project",
    )
    has_job_duty = fields.Selection(
        FIELD_SELECTION,
        "Duty",
        required=True,
        default="no",
        help="Display Duty field on project",
    )
    has_job_shipping_co = fields.Selection(
        FIELD_SELECTION,
        "Shipping Co.",
        required=True,
        default="no",
        help="Display Shipping Co. field on project",
    )
    has_job_terminal_payment = fields.Selection(
        FIELD_SELECTION,
        "Terminal Payment",
        required=True,
        default="no",
        help="Display Terminal Payment field on project",
    )
    has_custom_release_date = fields.Selection(
        FIELD_SELECTION,
        "Custom Release Date",
        required=True,
        default="no",
        help="Display Custom Release Date field on project",
    )
    has_job_tdo = fields.Selection(
        FIELD_SELECTION,
        "TDO",
        required=True,
        default="no",
        help="Display TDO field on project",
    )
    has_job_plant_delivery_date = fields.Selection(
        FIELD_SELECTION,
        "Plant delivery date",
        required=True,
        default="no",
        help="Display Plant delivery date field on project",
    )
    has_exchange_control_returned = fields.Selection(
        FIELD_SELECTION,
        "Exchange control returned",
        required=True,
        default="no",
        help="Display Exchange control returned field on project",
    )

    has_shipping_rating_till = fields.Selection(
        FIELD_SELECTION,
        "Shipping Rating Till",
        required=True,
        default="no",
        help="Display Shipping Rating Till field on project",
    )
    has_terminal_rating_till = fields.Selection(
        FIELD_SELECTION,
        "Terminal Rating Till",
        required=True,
        default="no",
        help="Display Terminal Rating Till field on project",
    )
    has_cleared_date = fields.Selection(
        FIELD_SELECTION,
        "Cleared Date",
        required=True,
        default="no",
        help="Display Cleared Date field on project",
    )
    has_loading_date = fields.Selection(
        FIELD_SELECTION,
        "Loading Date",
        required=True,
        default="no",
        help="Display Loading Date field on project",
    )
    has_delivery_date = fields.Selection(
        FIELD_SELECTION,
        "Delivery Date",
        required=True,
        default="no",
        help="Display Delivery Date field on project",
    )
    has_container_return_date = fields.Selection(
        FIELD_SELECTION,
        "Container Return Date",
        required=True,
        default="no",
        help="Display Container Return Date field on project",
    )
    has_total_cycle = fields.Selection(
        FIELD_SELECTION,
        "Total Cycle",
        required=True,
        default="no",
        help="Display Total Cycle field on project",
    )
    has_job_do = fields.Selection(
        FIELD_SELECTION,
        "DO",
        required=True,
        default="no",
        help="Display DO field on project",
    )
    has_ecd_date = fields.Selection(
        FIELD_SELECTION,
        "ECD Date",
        required=True,
        default="no",
        help="Display ECD date field on project",
    )
    has_refund_demurrage = fields.Selection(
        FIELD_SELECTION,
        "Refund/Demurrage",
        required=True,
        default="no",
        help="Display Refund  Demurrage section on project",
    )
    has_cdr = fields.Selection(
        FIELD_SELECTION,
        "CDR",
        required=True,
        default="no",
        help="Display CDR section on project",
    )
    has_etr = fields.Selection(
        FIELD_SELECTION,
        "ETR",
        required=True,
        default="no",
        help="Display ETR section on project",
    )

    has_etd = fields.Selection(
        FIELD_SELECTION,
        "ETD",
        required=True,
        default="optional",
        help="Display ETD section on project",
    )
    has_eta = fields.Selection(
        FIELD_SELECTION,
        "ETA",
        required=True,
        default="optional",
        help="Display ETA section on project",
    )
    has_ata = fields.Selection(
        FIELD_SELECTION,
        "ATA",
        required=True,
        default="no",
        help="Display ATA section on project",
    )
    has_discharge_date = fields.Selection(
        FIELD_SELECTION,
        "Discharge Date",
        required=True,
        default="no",
        help="Display discharge date section on project",
    )
    has_doc_to_agent = fields.Selection(
        FIELD_SELECTION,
        "Doc. to agent",
        required=True,
        default="no",
        help="Display date document was sent to agent on project",
    )
    has_rotation_number = fields.Selection(
        FIELD_SELECTION,
        "Rotation Number",
        required=True,
        default="no",
        help="Display rotation number section on project",
    )
    has_nafdac_1_stamp_date = fields.Selection(
        FIELD_SELECTION,
        "NAFDAC 1st stamp date",
        required=True,
        default="no",
        help="Display NAFDAC 1st stamp date section on project",
    )
    has_nafdac_2_stamp_date = fields.Selection(
        FIELD_SELECTION,
        "NAFDAC 2nd stamp sate",
        required=True,
        default="no",
        help="Display NAFDAC 2nd stamp date section on project",
    )
    has_son_date = fields.Selection(
        FIELD_SELECTION,
        "SON date",
        required=True,
        default="no",
        help="Display SON date section on project",
    )
    has_pod = fields.Selection(
        FIELD_SELECTION,
        "POD",
        required=True,
        default="no",
        help="Display POD section on project",
    )
    has_free_days = fields.Selection(
        FIELD_SELECTION,
        "No of Free days",
        required=True,
        default="optional",
        help="Display POD section on project",
    )
    has_custom_exam_date = fields.Selection(
        FIELD_SELECTION,
        "Custom Exams Booking Date",
        required=True,
        default="no",
        help="Display Custom Exams Booking Date section on project",
    )
    has_custom_date = fields.Selection(
        FIELD_SELECTION,
        "Custom Exams Date",
        required=True,
        default="no",
        help="Display Custom Exams Booking Date section on project",
    )
    has_fou_release_date = fields.Selection(
        FIELD_SELECTION,
        "FOU release Date",
        required=True,
        default="no",
        help="Display FUR release Date section on project",
    )
    has_gate_release_date = fields.Selection(
        FIELD_SELECTION,
        "Gate release Date",
        required=True,
        default="no",
        help="Display Gate release Date section on project",
    )

    _order = "name"

    _sql_constraints = [
        ("name_uniq", "UNIQUE (name)", "Name already exists."),
    ]

    def _compute_default_task_count(self):
        for project in self:
            default_task = self.env["project.task"].search(
                [("is_category_task", "=", True), ("project_categ_id", "=", project.id)]
            )
            project.default_task_count = len(default_task)

    def _compute_task_count(self):
        for project in self:
            task = project.project_category_task_ids.search(
                [
                    ("project_categ_id", "=", project.id),
                    ("is_category_task", "=", False),
                ]
            )
            project.task_count = len(task)

    def _compute_task_needaction_count(self):
        projects_data = self.env["project.task"].read_group(
            [("project_categ_id", "in", self.ids), ("message_needaction", "=", True)],
            ["project_categ_id"],
            ["project_categ_id"],
        )
        mapped_data = {
            project_data["project_categ_id"][0]: int(project_data["project_categ_id_count"])
            for project_data in projects_data
        }
        for project in self:
            project.task_needaction_count = mapped_data.get(project.id, 0)


class ProjectProject(models.Model):
    _inherit = "project.project"

    project_categ_id = fields.Many2one(
        "project.project.category",
        "Job Dynamics",
        domain="[('project_type_id', '=', type_id)]",
        required=True,
    )

    has_job_form_m = fields.Selection(
        [],
        "Has Job Form M",
        related="project_categ_id.has_job_form_m",
        readonly=True,
        default="no",
    )
    has_job_form_m_date = fields.Selection(
        [],
        "Form M. Date",
        related="project_categ_id.has_job_form_m_date",
        readonly=True,
        default="no",
    )
    has_bol_awb_ref = fields.Selection(
        [],
        "BOL/AWB Ref",
        related="project_categ_id.has_bol_awb_ref",
        readonly=True,
        default="no",
    )
    has_arrival_date = fields.Selection(
        [],
        "Arrival Date",
        related="project_categ_id.has_arrival_date",
        readonly=True,
        default="no",
    )
    has_job_son = fields.Selection([], "SON", related="project_categ_id.has_job_son", readonly=True, default="no")
    has_job_liner = fields.Selection(
        [],
        "LINER",
        related="project_categ_id.has_job_liner",
        readonly=True,
        default="no",
    )
    has_job_ba_number = fields.Selection(
        [],
        "BA Number",
        related="project_categ_id.has_job_ba_number",
        readonly=True,
        default="no",
    )
    has_job_cbm = fields.Selection([], "CBM", related="project_categ_id.has_job_cbm", readonly=True, default="no")
    has_bill_of_lading = fields.Selection(
        [],
        "Bill of Lading",
        related="project_categ_id.has_bill_of_lading",
        readonly=True,
        default="no",
    )
    has_shipping_doc = fields.Selection(
        [],
        "Shipping Doc",
        related="project_categ_id.has_shipping_doc",
        readonly=True,
        default="no",
    )
    has_job_paar = fields.Selection([], "PAAR", related="project_categ_id.has_job_paar", readonly=True, default="no")
    has_job_assessment = fields.Selection(
        [],
        "Assessment",
        related="project_categ_id.has_job_assessment",
        readonly=True,
        default="no",
    )
    has_job_duty = fields.Selection([], "Duty", related="project_categ_id.has_job_duty", readonly=True, default="no")
    has_job_shipping_co = fields.Selection(
        [],
        "Shipping Co.",
        related="project_categ_id.has_job_shipping_co",
        readonly=True,
        default="no",
    )
    has_job_terminal_payment = fields.Selection(
        [],
        "Terminal Payment",
        related="project_categ_id.has_job_terminal_payment",
        readonly=True,
        default="no",
    )
    has_custom_release_date = fields.Selection(
        [],
        "Custom Release Date",
        related="project_categ_id.has_custom_release_date",
        readonly=True,
        default="no",
    )
    has_job_tdo = fields.Selection([], "TDO", related="project_categ_id.has_job_tdo", readonly=True, default="no")
    has_job_plant_delivery_date = fields.Selection(
        [],
        "Plant delivery date",
        related="project_categ_id.has_job_plant_delivery_date",
        readonly=True,
        default="no",
    )
    has_exchange_control_returned = fields.Selection(
        [],
        "Exchange control returned",
        related="project_categ_id.has_exchange_control_returned",
        readonly=True,
        default="no",
    )
    has_shipping_rating_till = fields.Selection(
        [],
        "Shipping Rating Till",
        related="project_categ_id.has_shipping_rating_till",
        readonly=True,
        default="no",
    )
    has_terminal_rating_till = fields.Selection(
        [],
        "Terminal Rating Till",
        related="project_categ_id.has_terminal_rating_till",
        readonly=True,
        default="no",
    )
    has_cleared_date = fields.Selection(
        [],
        "Cleared Date",
        related="project_categ_id.has_cleared_date",
        readonly=True,
        default="no",
    )
    has_loading_date = fields.Selection(
        [],
        "Loading Date",
        related="project_categ_id.has_loading_date",
        readonly=True,
        default="no",
    )
    has_delivery_date = fields.Selection(
        [],
        "Delivery Date",
        related="project_categ_id.has_delivery_date",
        readonly=True,
        default="no",
    )
    has_container_return_date = fields.Selection(
        [],
        "Container Return Date",
        related="project_categ_id.has_container_return_date",
        readonly=True,
        default="no",
    )
    has_total_cycle = fields.Selection(
        [],
        "Total Cycle",
        related="project_categ_id.has_total_cycle",
        readonly=True,
        default="no",
    )
    has_job_do = fields.Selection([], "DO", related="project_categ_id.has_job_do", readonly=True, default="no")
    has_ecd_date = fields.Selection([], "ECD Date", related="project_categ_id.has_ecd_date", readonly=True)
    has_refund_demurrage = fields.Selection(
        [],
        "Refund/Demurrage",
        related="project_categ_id.has_refund_demurrage",
        readonly=True,
    )
    has_cdr = fields.Selection([], "CDR", related="project_categ_id.has_cdr", readonly=True)
    has_etr = fields.Selection([], "ETR", related="project_categ_id.has_etr", readonly=True)

    has_etd = fields.Selection([], "ETD", related="project_categ_id.has_etd", readonly=True)
    has_eta = fields.Selection([], "ETA", related="project_categ_id.has_eta", readonly=True)
    has_ata = fields.Selection([], "ATA", related="project_categ_id.has_ata", readonly=True)
    has_discharge_date = fields.Selection(
        [],
        "Discharge Date",
        related="project_categ_id.has_discharge_date",
        readonly=True,
    )
    has_doc_to_agent = fields.Selection([], "Doc. to agent", related="project_categ_id.has_doc_to_agent", readonly=True)
    has_rotation_number = fields.Selection(
        [],
        "Rotation Number",
        related="project_categ_id.has_rotation_number",
        readonly=True,
    )
    has_nafdac_1_stamp_date = fields.Selection(
        [],
        "NAFDAC 1st stamp date",
        related="project_categ_id.has_nafdac_1_stamp_date",
        readonly=True,
    )
    has_nafdac_2_stamp_date = fields.Selection(
        [],
        "NAFDAC 2nd stamp sate",
        related="project_categ_id.has_nafdac_2_stamp_date",
        readonly=True,
    )
    has_son_date = fields.Selection([], "SON date", related="project_categ_id.has_son_date", readonly=True)
    has_pod = fields.Selection([], "POD", related="project_categ_id.has_pod", readonly=True)
    has_free_days = fields.Selection([], "No of Free days", related="project_categ_id.has_free_days", readonly=True)
    has_custom_exam_date = fields.Selection(
        [],
        "Custom Exams Booking Date",
        related="project_categ_id.has_custom_exam_date",
        readonly=True,
    )
    has_custom_date = fields.Selection(
        [],
        "Custom Exams Date",
        related="project_categ_id.has_custom_date",
        readonly=True,
    )
    has_fou_release_date = fields.Selection(
        [],
        "FOU release Date",
        related="project_categ_id.has_fou_release_date",
        readonly=True,
    )
    has_gate_release_date = fields.Selection(
        [],
        "Gate release Date",
        related="project_categ_id.has_gate_release_date",
        readonly=True,
    )

    @api.model
    def create(self, vals):
        result = super(ProjectProject, self).create(vals)
        if result and vals.get("project_categ_id"):
            # get project default tasks
            cat_id = vals.get("project_categ_id")
            if cat_id:
                proj_cat = self.env["project.project.category"].browse(int(cat_id))
                if proj_cat:
                    stage_ids = proj_cat.default_stage_ids.ids
                    result.write({"type_ids": [(6, 0, stage_ids)]})
                result._process_task(cat_id)

        return result

    def write(self, vals):
        if self.project_categ_id:
            if not self.type_ids:
                proj_cat = self.env["project.project.category"].browse(int(self.project_categ_id.id))
                if proj_cat:
                    stage_ids = proj_cat.default_stage_ids.ids
                    vals["type_ids"] = [(6, 0, stage_ids)]

        result = super(ProjectProject, self).write(vals)
        return result

    def _process_task(self, category_id):
        if category_id:
            proj_category_task = (
                self.env["project.task"]
                .sudo()
                .search(
                    [
                        ("project_categ_id", "=", int(category_id)),
                        ("is_category_task", "=", True),
                    ]
                )
            )
            if proj_category_task:
                for task in proj_category_task:
                    task_owner_id = task.task_assign_id.id if task.task_assign_id else False
                    task_user_id = task.task_assign_id.user_id.id if task.task_assign_id.user_id else self.user_id.id
                    task_dept = task.department_id if task.department_id else []
                    dept_id = task_dept.id if task_dept else False
                    admin_id = self.env.ref("base.user_root").id
                    if admin_id == task_user_id:
                        task_user_id = self.user_id.id
                        d_emp_rec = self.user_id._get_related_employees()
                        if d_emp_rec:
                            task_owner_id = d_emp_rec[0].id
                    if not task_owner_id and task_dept:
                        if not task_owner_id in task_dept.member_ids.ids:
                            if task_dept.manager_id:
                                task_owner_id = task_dept.manager_id.id
                                if task_owner_id:
                                    task_user_id = task_dept.manager_id.user_id.id

                    if not task_owner_id:
                        emp_rec = self.user_id._get_related_employees()
                        if emp_rec:
                            dept_id = emp_rec[0].department_id.id or False
                            task_owner_id = emp_rec[0].id
                            task_user_id = emp_rec[0].user_id.id

                    if not dept_id and task_owner_id:
                        dept_rec = self.env["hr.employee"].sudo().browse(int(task_owner_id))
                        if dept_rec:
                            dept_id = dept_rec.department_id.id if dept_rec.department_id else False

                    task_name = "%s (%s)" % (task.name, self.name)
                    # compute task start date, end date and escalation start date
                    str_dur = task.task_duration_days or 1
                    esl_dur = task.task_escalation_days or 2
                    comp_str_date = datetime.now() + relativedelta(days=int(str_dur))
                    comp_els_date = comp_str_date + relativedelta(days=int(esl_dur))
                    end_date = comp_str_date.strftime("%Y-%m-%d")
                    esl_date = comp_els_date.strftime("%Y-%m-%d")
                    task.with_context(mail_notrack=True).copy(
                        {
                            "project_id": self.id,
                            "task_assign_id": task_owner_id,
                            "user_id": task_user_id,
                            "department_id": dept_id,
                            "is_category_task": False,
                            "partner_id": self.partner_id.id,
                            "task_escalation_days": esl_dur,
                            "task_duration_days": str_dur,
                            "task_start_date": datetime.now().strftime("%Y-%m-%d"),
                            "task_end_date": end_date,
                            "date_deadline": end_date,
                            "date_assign": datetime.now().strftime("%Y-%m-%d"),
                            "task_escalation_trigger": esl_date,
                            # "creation_date": datetime.now().strftime("%Y-%m-%d"),
                            "create_date": datetime.now().strftime("%Y-%m-%d"),
                            "create_uid": self.user_id.id,
                            "name": task_name,
                        }
                    )
