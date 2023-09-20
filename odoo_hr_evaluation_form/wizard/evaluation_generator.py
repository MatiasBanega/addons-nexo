from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class EvaluationGenerator(models.Model):

    _name = 'evaluation.generator'
    _description = 'Generate evaluation for many employees at the same time.'

    evaluator_id = fields.Many2one('res.users', required=True)
    evaluation_plan_id = fields.Many2one('hr_evaluation.plan', required=True)
    evaluation_date = fields.Date(
        required=True, default=fields.Date.context_today)
    employees_ids = fields.Many2many('hr.employee', 'evaluation_employee_rel')

    def generate_evaluations(self):
        '''Generate the employee evaluations and throw the  tree view with
        the results.

        '''
        HrEvaluation = self.env['hr_evaluation.evaluation']
        evaluations = []
        for employee in self.employees_ids:
            evaluation = HrEvaluation.create(
                {'date' : self.evaluation_date,
                 'employee_id': employee.id,
                 'evaluation_officer_id': self.evaluator_id.id,
                 'company_id': self.env.company.id,
                 'plan_id': self.evaluation_plan_id.id})
            evaluations.append(evaluation.id)
        eval_tree_view = self.env.ref('odoo_hr_evaluation_form.view_hr_evaluation_tree')
        eval_form_view = self.env.ref('odoo_hr_evaluation_form.view_hr_evaluation_form')
        return {'name': _('Generated Evaluations'),
                'res_model': 'hr_evaluation.evaluation',
                'domain': [('id', 'in', evaluations)],
                'views': [(eval_tree_view.id, 'tree'),(eval_form_view.id, 'form')],
                'context': self.env.context,
                'type': 'ir.actions.act_window'}

    @api.model
    def default_get(self, default_fields):
        '''Redefined for add the relationship with the selected employees.'''
        rec = super(EvaluationGenerator, self).default_get(default_fields)
        active_ids = (self._context.get('active_ids') or
                      self._context.get('active_id'))
        rec.update({'employees_ids': [(6, 0, active_ids)]})
        return rec

