# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError


class HrEvaluationPerformance(models.Model):
    _name = 'hr.evalution.performance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Evalution Form'
    _order = 'id desc'
    
    name = fields.Char(
        string='Name',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    employee_id = fields.Many2one(
        'hr.employee',
        'Employee',
        required=True,
        readonly=True,
    )
    date = fields.Date(
        'Date',
        required=True,
    )
    job_title_id = fields.Many2one(
        'hr.job',
        'Job Title',
        related="employee_id.job_id"
    )
    empl_department_id = fields.Many2one(
        'hr.department',
        string='Department',
        related='employee_id.department_id'
    )
    performance_introduction = fields.Text(
        'Introduction',
    )
    reviewer_id = fields.Many2one(
        "hr.employee",
        "Reviewer's Name",
    )
    review_period_start_date = fields.Date(
        'Review Start Date'
    )
    review_period_end_date = fields.Date(
        'Review End Date'
    )
    first_competencies_ids = fields.One2many(
        'employee.competencies.objectives',
        'evalution_performance_id',
        string='First Part: Competencies',
        tracking=3
    )
    total_score_competencies = fields.Integer(
        'Total Score Competencies',
        compute="_compute_total_score_competencies",
        store=True
    )
    employee_comment = fields.Text(
        "First Part: Competencies Employee's Comments",
        tracking=3
    )
    reviewer_comment = fields.Text(
        "First Part: Competencies Reviewer’s Comments",
        tracking=3
    )
    second_objectives_ids = fields.One2many(
        'employee.competencies.objectives',
        'second_objectives_performance_id',
        string='Second Part: OBJECTIVES',
        tracking=3
    )
    total_score_objectives = fields.Integer(
        'Total Score Objectives',
        compute="_compute_total_score_objectives",
        store=True
    )
    employee_objectives_comment = fields.Text(
        "Second Part: OBJECTIVES Employee's Comments",
        tracking=3
    )
    reviewer_objectives_comment = fields.Text(
        "Second Part: OBJECTIVES Reviewer’s Comments",
        tracking=3
    )
    overall_score = fields.Integer(
        'Overall Score',
        compute="_compute_overall_scrore",
        store=True
    )
    employee_overall_comment = fields.Text(
        "Employee's Overall's Comments",
        tracking=3
    )
    reviewer_overall_comments = fields.Text(
        "Reviewer’s Overall's Comments",
        tracking=3
    )
    development_plan = fields.Html(
         'Development Plan',
        tracking=3
    )
    state = fields.Selection(
        selection=[
            ('draft', 'New'),
            ('confirmed', 'Confirmed'),
            # ('approved', 'Approved'),
            ('submited', 'Submited'),

        ],
        default='draft',
        copy=False,
        readonly=True,
        tracking=3
    )
    evalution_appraisal_id = fields.Many2one(
        'hr_evaluation.evaluation',
        'Evaluation Appraisal',
        copy=False,
    )
    evalution_officer_id = fields.Many2one(
        'res.users',
        related='evalution_appraisal_id.evaluation_officer_id',
        store=True,
    )
    empl_department_id = fields.Many2one(
        'hr.department',
        string='Department',
        related='employee_id.department_id'
    )
    is_user_employee = fields.Boolean(
        string='User Employee',
        compute='_compute_user_employee'
    )
    is_user_reviewer = fields.Boolean(
        string='User Reviewer',
        compute='_compute_user_reviewer'
    )
    is_user_officer = fields.Boolean(
        string='User Officer',
        compute='_compute_user_officer'
    )
    eval_employee_acknowledge = fields.Text(
        'Employee Acknoledgement',
        copy=False,
    )
    eval_reviewer_acknowledge = fields.Text(
        'Reviewer Acknoledgement',
        copy=False,
    )
    is_discussed = fields.Boolean(
        'Discussed',
        copy=False,
        readonly=True,
    )
    signature = fields.Image(
        'Signature',
        help='Signature',
        copy=False,
        attachment=True
    )
    performance_seq = fields.Integer(
        'Sequence',
        copy=False,
    )
    phase_id =fields.Many2one(
        'hr_evaluation.plan.phase',
        string='Appraisal Phase',
        required=True
    )
    is_signed = fields.Boolean(
        'Is Signed',
        compute="_compute_is_signed"
    )
    company_id = fields.Many2one(
        'res.company', 
        string='Company', 
        required=True,
        default=lambda self: self.env.user.company_id
        )
    
    @api.depends('signature')
    def _compute_is_signed(self):
        for performance in self:
            performance.is_signed = performance.signature

    @api.depends('first_competencies_ids', 'first_competencies_ids.reviewer_points_id')
    def _compute_total_score_competencies(self):
        for rec in self:
            reviewer_points = 0
            for first_competencies_id in rec.first_competencies_ids:
                reviewer_points += first_competencies_id.reviewer_points_id.name
            rec.total_score_competencies = reviewer_points

    @api.depends('second_objectives_ids', 'second_objectives_ids.reviewer_points_id')
    def _compute_total_score_objectives(self):
        for rec in self:
            reviewer_points = 0
            for second_objectives_id in rec.second_objectives_ids:
                reviewer_points += second_objectives_id.reviewer_points_id.name
            rec.total_score_objectives = reviewer_points

    @api.depends('total_score_competencies', 'total_score_objectives')
    def _compute_overall_scrore(self):
        for rec in self:
            rec.overall_score = rec.total_score_competencies + rec.total_score_objectives

    def _compute_user_employee(self):
        for rec in self:
            if self._uid == rec.employee_id.user_id.id:
                rec.is_user_employee = True
            else:
                rec.is_user_employee = False

    def _compute_user_reviewer(self):
        for rec in self:
            print('-----------rec------------',rec)
            if self._uid == rec.reviewer_id.user_id.id:
                print('-------------self._uid--2--------',self._uid)
                rec.is_user_reviewer = True
            else:
                rec.is_user_reviewer = False

    def _compute_user_officer(self):
        for rec in self:
            if self._uid == rec.evalution_officer_id.id:
                rec.is_user_officer = True
            else:
                rec.is_user_officer = False

    def get_evaluation_link(self):
        self.ensure_one()
        base_url = self.get_base_url()
        return base_url+'/evaluation/%d' % (self.id)

    def button_confirmed(self):
        self.ensure_one()
        self = self.sudo()
        if self.reviewer_id.user_id.id != self._uid and self.evalution_officer_id.id != self._uid:
            raise UserError(_("Only a reviewer of the document can submit the record. So if you are set as a reviewer of the document then only you can submit it."))
        performance_eval_id = self.evalution_appraisal_id.performance_ids.filtered(
                    lambda performance_id: performance_id.phase_id.wait
                    and performance_id.state != 'submited'
                    and performance_id.performance_seq == self.performance_seq - 1)
        if performance_eval_id:
            raise UserError(_("Not Allow to confirm untill Previous Performance(s) are not Submited."))
        self.action_performance_confirmed()
    
    def action_performance_confirmed(self):
        self.ensure_one()
        template_id = self.env.ref('odoo_hr_evaluation_form.evaluation_performance_send_confirm_by_empl_mail_tmpl')
        template_id.send_mail(self.id)
        self.write({
            'state': 'confirmed'
        })

    def button_approve_by_reviewer(self):
        self.ensure_one()
        if self.reviewer_id.user_id.id != self._uid and self.evalution_officer_id.id != self._uid:
            raise UserError(_("Only a reviewer of the document can submit the record. So if you are set as a reviewer of the document then only you can submit it."))
        if any(not competencies.reviewer_points_id for competencies in self.first_competencies_ids):
            raise UserError(_("Competencies/Objectives Rewards remain to add"))
        if any(not objectives.reviewer_points_id for objectives in self.second_objectives_ids):
            raise UserError(_("Competencies/Objectives Rewards remain to add"))
        self = self.sudo()
        template_id = self.env.ref('odoo_hr_evaluation_form.evaluation_performance_send_approve_by_reviewer_mail_tmpl')
        template_id.send_mail(self.id)
        self.write({
            'state': 'submited'
        })
        self.performance_req_waiting_review()

    def performance_req_waiting_review(self):
        for performance in self:
            performance_eval_curr_seq_id = performance.evalution_appraisal_id.performance_ids.filtered(
                lambda performance_id: performance_id.phase_id.wait
                and performance_id.state != 'submited'
                and performance_id.performance_seq == performance.performance_seq)
            if not performance_eval_curr_seq_id:
                performance_eval_id = performance.evalution_appraisal_id.performance_ids.filtered(
                    lambda performance_id: performance_id.phase_id.wait
                    and performance_id.state != 'submited'
                    and performance_id.performance_seq == performance.performance_seq + 1)
                if performance_eval_id:
                    for performance_eval in performance_eval_id:
                        performance_eval.action_performance_confirmed()
        return True

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('hr.evalution.performance') or _('New')
        return super(HrEvaluationPerformance, self).create(vals)

    def unlink(self):   
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_("You can not delete Evaluation Form  once confirmed."))
        return super(HrEvaluationPerformance, self).unlink()


class FirstCompetencies(models.Model):
    _name = 'employee.competencies.objectives'
    _description = 'First Competencies'
    _rec_name = 'competencies_objectives_id'

    evalution_performance_id = fields.Many2one(
        'hr.evalution.performance',
    )
    second_objectives_performance_id = fields.Many2one(
        'hr.evalution.performance',
    )
    employee_id = fields.Many2one(
        'hr.employee',
        'Employee',
        related="evalution_performance_id.employee_id"
    )
    reviewer_id = fields.Many2one(
        'hr.employee',
        "Reviewer Name",
        required=False,
        related="evalution_performance_id.reviewer_id",
        store=True
    )
    competencies_objectives_id = fields.Many2one(
        'competencies.objectives',
        'Name',
        required=True,
    )
    employee_points_id = fields.Many2one(
        'performance.rating.custom',
        string='EE',
    )
    reviewer_points_id = fields.Many2one(
        'performance.rating.custom',
        string='R',
    )
    second_objectives_performance_id = fields.Many2one(
        'hr.evalution.performance',
    )
    evalution_performance_state = fields.Selection(
        related="evalution_performance_id.state",
        store=True
    )
    second_objectives_performance_state = fields.Selection(
        related='second_objectives_performance_id.state',
        store=True,
    )

    def _check_reward_change_access(self, values):
        rec = self
        if rec.evalution_performance_id:
            if rec.evalution_performance_state == 'draft' and values.get('reviewer_points_id') and self.env.uid not in [rec.reviewer_id.user_id.id, rec.evalution_performance_id.evalution_officer_id.id]:
                raise UserError(_("COMPETENCIES: You can not update the value of the reviewer column since you are not a reviewer of the document."))

            if rec.evalution_performance_state == 'confirmed' and values.get('employee_points_id') and self.env.uid not in [rec.reviewer_id.user_id.id, rec.evalution_performance_id.evalution_officer_id.id]:
                raise UserError(_("COMPETENCIES: You can not update the value of your self-assessment (EE) column point since the document has been confirmed."))
            if rec.evalution_performance_state == 'confirmed' and values.get('reviewer_points_id') and self.env.uid not in [rec.reviewer_id.user_id.id, rec.evalution_performance_id.evalution_officer_id.id]:
                raise UserError(_("COMPETENCIES: You can not update the value of the reviewer (R) column point."))

            if rec.evalution_performance_state == 'wait_officer_approval' and values.get('employee_points_id') and self.env.uid not in [rec.evalution_performance_id.evalution_officer_id.id]:
                raise UserError(_("COMPETENCIES: You can not change the value of the employee column at this stage since you are not an evaluation officer."))
            if rec.evalution_performance_state == 'wait_officer_approval' and values.get('reviewer_points_id') and self.env.uid not in [rec.evalution_performance_id.evalution_officer_id.id]:
                raise UserError(_("COMPETENCIES: You can not change the value of the reviewer point column at this stage since you are not an evaluation officer."))
        
        if rec.second_objectives_performance_id:
            if rec.second_objectives_performance_state == 'draft' and values.get('reviewer_points_id') and self.env.uid not in [rec.second_objectives_performance_id.reviewer_id.user_id.id, rec.second_objectives_performance_id.evalution_officer_id.id]:
                raise UserError(_("OBJECTIVES: You can not update the value of the reviewer column since you are not a reviewer of the document."))

            if rec.second_objectives_performance_state == 'confirmed' and values.get('employee_points_id') and self.env.uid not in [rec.second_objectives_performance_id.reviewer_id.user_id.id, rec.second_objectives_performance_id.evalution_officer_id.id]:
                raise UserError(_("OBJECTIVES: You can not update the value of your self-assessment (EE) column point since the document has been confirmed."))
            if rec.second_objectives_performance_state == 'confirmed' and values.get('reviewer_points_id') and self.env.uid not in [rec.second_objectives_performance_id.reviewer_id.user_id.id, rec.second_objectives_performance_id.evalution_officer_id.id]:
                raise UserError(_("OBJECTIVES: You can not update the value of the reviewer (R) column point."))

            if rec.second_objectives_performance_state == 'wait_officer_approval' and values.get('employee_points_id') and self.env.uid not in [rec.second_objectives_performance_id.evalution_officer_id.id]:
                raise UserError(_("OBJECTIVES: You can not change the value of the employee column at this stage since you are not an evaluation officer."))
            if rec.second_objectives_performance_state == 'wait_officer_approval' and values.get('reviewer_points_id') and self.env.uid not in [rec.second_objectives_performance_id.evalution_officer_id.id]:
                raise UserError(_("OBJECTIVES: You can not change the value of the reviewer point column at this stage since you are not an evaluation officer."))

        return True

    def write(self, values):
        rating_obj = self.env['performance.rating.custom']
        result = super(FirstCompetencies, self).write(values)
        for rec in self:
            rec._check_reward_change_access(values)
            msg = 'The Perfomance Values are updated:'
            if values.get('name'):
                msg += '<br/>'+values.get('name')
            else:
                msg +=  '<br/>'+rec.competencies_objectives_id.name
            if values.get('employee_points_id'):
                msg += '<br/>'+str(rec.employee_points_id.name) +'->'+ str(rating_obj.browse(values.get('employee_points_id')).name)
            if values.get('reviewer_points_id'):
                msg += '<br/>'+str(rec.reviewer_points_id.name) +'->'+ str(rating_obj.browse(values.get('reviewer_points_id')).name)
            if rec.evalution_performance_id:
                rec.evalution_performance_id.message_post(body=msg)
            elif rec.second_objectives_performance_id:
                rec.second_objectives_performance_id.message_post(body=msg)
        return result


class Rating(models.Model):
    _name = 'performance.rating.custom'
    _description = 'Evaluation Form Ratings'
    _order = 'sequence'

    name = fields.Integer(
        'Rating',
        required=True,
    )
    sequence = fields.Integer(
        'Sequence',
        required=True,
    )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

