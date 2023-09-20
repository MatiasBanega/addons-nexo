# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from dateutil import parser
import time
from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DF

class HrEvaluationPlan(models.Model):
    _name = "hr_evaluation.plan"
    _description = "Appraisal Plan"

    name = fields.Char(string='Appraisal Plan', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)
    phase_ids = fields.One2many('hr_evaluation.plan.phase', 'plan_id',
                                string='Appraisal Phases', copy=True)
    competencies_objectives_tmpl_id = fields.Many2one(
        'evalution.competencies.objectives.template',
        'Evaluation Question Template',
        # required=True,
    )
    active = fields.Boolean(string='Active', default=True)


class HrEvaluationPlanPhase(models.Model):
    _name = "hr_evaluation.plan.phase"
    _description = "Appraisal Plan Phase"
    _order = "sequence"

    name = fields.Char(string='Phase', required=True)
    sequence = fields.Integer(string='Sequence', default=1)
    company_id = fields.Many2one('res.company', related='plan_id.company_id',
                                 string='Company', store=True, readonly=True)
    plan_id = fields.Many2one('hr_evaluation.plan', string='Appraisal Plan')
    action = fields.Selection([('top-down', 'Top-Down Appraisal Requests'),
                               ('bottom-up', 'Bottom-Up Appraisal Requests'),
                               ('self', 'Self Appraisal Requests'),
                               ('final', 'Final Interview')], 
                              string='Action',
                              required=True)
    competencies_objectives_tmpl_id = fields.Many2one(
        'evalution.competencies.objectives.template',
        'Evaluation Question Template',
        required=True,
    )
    wait = fields.Boolean(string='Wait Previous Phases',
                          help="Check this box if you want to wait that all preceding phases are finished before launching this phase.")


class hr_evaluation(models.Model):
    _name = "hr_evaluation.evaluation"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Employee Appraisal"
    _rec_name = "employee_id"

    date = fields.Date(string="Appraisal Deadline",
        default=lambda *a: (
            parser.parse(datetime.now().strftime('%Y-%m-%d')) + relativedelta(
                months=+1)).strftime('%Y-%m-%d'), required=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    note_summary = fields.Text(string='Appraisal Summary')
    note_action = fields.Text(string='Action Plan', help="If the evaluation does not meet the expectations, you can propose an action plan")
    rating = fields.Selection([('0', 'Significantly below expectations'),
                               ('1', 'Do not meet expectations'),
                               ('2', 'Meet expectations'),
                               ('3', 'Exceeds expectations'),
                               ('4', 'Significantly exceeds expectations')],
                              string="Appreciation",
                              help="This is the appreciation on which the evaluation is summarized.")
    plan_id = fields.Many2one('hr_evaluation.plan', string='Plan', required=True)
    state = fields.Selection([('draft', 'New'),
                              ('cancel', 'Cancelled'),
                              ('wait', 'Plan In Progress'),
                              ('progress', 'Waiting Appreciation'),
                              ('done', 'Done')], string='Status', required=False,
                             readonly=True, copy=False, default='draft')
    date_close = fields.Date(string='Ending Date')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self:self.env.user.company_id.id)
    evaluation_officer_id = fields.Many2one('res.users', string='Evaluation  HR/Officer', default = lambda self: self.env.user.id)
    
    hr_evalution_performance_id = fields.Many2one(
        'hr.evalution.performance',
        'Evaluation Form',
        copy=False,
        readonly=True,
    )
    manager_id = fields.Many2one(
        'hr.employee',
        'Employee Manager',
    )
    performance_ids = fields.One2many(
        'hr.evalution.performance',
        'evalution_appraisal_id',
        string='Evaluation Forms',
    )
    review_period_start_date = fields.Date(
        'Review Start Date'
    )
    review_period_end_date = fields.Date(
        'Review End Date'
    )

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        self.manager_id = self.employee_id.parent_id.id or self.employee_id.department_id.manager_id.id

    def massive_start_appraisal(self):
        '''Massive start of appraisals.'''
        for app in self.search([('id', 'in', self._context.get('active_ids'))]):
            app.button_plan_in_progress()

    def name_get(self):
        res = []
        for record in self:
            name = record.plan_id.name
            employee = record.employee_id.name
            res.append((record['id'], name + ' / ' + employee))
        return res

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        vals = {'plan_id': False}
        if self.employee_id:
            for employee in self.env['hr.employee'].browse(self.employee_id.id):
                if (employee and employee.evaluation_plan_id_custom
                    and employee.evaluation_plan_id_custom.id):
                    vals.update({'plan_id': employee.evaluation_plan_id_custom.id})
        return {'value': vals}

    def _prepare_first_competencies_vals(self, competencies_objectives_tmpl_id):
        vals_lst = []
        for competencies_id in competencies_objectives_tmpl_id.competencies_line_ids:
            vals_lst.append(
                (0, 0, {
                    'competencies_objectives_id': competencies_id.competencies_objectives_id.id,
                })
            )
        return vals_lst

    def _prepare_second_objective_vals(self, competencies_objectives_tmpl_id):
        vals_lst = []
        for objective_id in competencies_objectives_tmpl_id.objectives_line_ids:
            vals_lst.append(
                (0, 0, {
                    'competencies_objectives_id': objective_id.competencies_objectives_id.id,
                })
            )
        return vals_lst

    def _prepare_evalution_performance_vals_dummy(self):
        return {
            'employee_id': self.employee_id.id,
            'reviewer_id': self.manager_id.id or self.employee_id.parent_id.id or self.employee_id.department_id.manager_id.id,
            'date': self.date,
            'evalution_appraisal_id': self.id,
            'first_competencies_ids': self._prepare_first_competencies_vals(),
            'second_objectives_ids': self._prepare_second_objective_vals(),

        }

    def _start_evalution_performance_dummy(self):
        evalution_performance_vals = self._prepare_evalution_performance_vals()
        return self.env['hr.evalution.performance'].sudo().create(evalution_performance_vals)

    def button_plan_in_progress(self):
        for evaluation in self:
            wait = False
            performance_seq = 1
            prev_phase = False
            for phase in evaluation.plan_id.phase_ids:
                children = []
                if phase.action == "final":
                    children = evaluation.evaluation_officer_id.employee_id
                elif phase.action == "bottom-up":
                    children = evaluation.employee_id.child_ids
                elif phase.action == "top-down":
                    if evaluation.employee_id.parent_id:
                        children = evaluation.employee_id.parent_id
                elif phase.action == "self":
                    children = evaluation.employee_id

                performance_id = False
                for child in children:
                    performance_id = self.env['hr.evalution.performance'].sudo().create({
                        'employee_id': self.employee_id.id,
                        'reviewer_id': child.id,
                        'date': self.date,
                        'performance_introduction': phase.competencies_objectives_tmpl_id.performance_introduction,
                        'evalution_appraisal_id': self.id,
                        'first_competencies_ids': self._prepare_first_competencies_vals(phase.competencies_objectives_tmpl_id),
                        'second_objectives_ids': self._prepare_second_objective_vals(phase.competencies_objectives_tmpl_id),
                        'performance_seq': performance_seq,
                        'phase_id': phase.id,
                        'review_period_start_date' : self.review_period_start_date,
                        'review_period_end_date' : self.review_period_end_date,

                    })
                if phase.wait:
                    wait = True
                if performance_seq == 1:
                    performance_id.action_performance_confirmed()
                if not wait and performance_id:
                    performance_id.performance_req_waiting_review()
                performance_seq += 1
        self.write({'state': 'wait'})
        return True

    def open_employee_performance(self):
        action = self.env.ref('odoo_hr_evaluation_form.action_hr_evalution_performance').read()[0]
        action['domain'] = [('evalution_appraisal_id', '=', self.id)]
        return action

    def button_final_validation(self):
        '''Set validated state to the appraisal, also send an email for
        the evaluated user.
        '''
        self.write({'state': 'progress'})
        for evaluation in self:
            if (evaluation.employee_id and
                evaluation.employee_id.parent_id and
                evaluation.employee_id.parent_id.user_id.partner_id):
                   evaluation.message_subscribe(
                       partner_ids=[
                           evaluation.employee_id.parent_id.user_id.partner_id.id])
            if evaluation.performance_ids.filtered(lambda performance:performance.state != 'submited'):
                msg_err = "You cannot change state, because some appraisal" +\
                          " forms have not been completed."
                raise UserError(_(msg_err))
        return True

    def button_cancel(self):
        self.write({'state': 'cancel'})
        return True

    def button_draft(self):
        self.write({'state': 'draft'})
        return True
