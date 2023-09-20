# © 2021 onDevelop.sa
# Autor: Idelis Gé Ramírez


from odoo import api, fields, models, _


class HrEmployee(models.Model):
    _inherit="hr.employee"
    _description="Employee redefinition for add some needed functions."

    def register_evaluation(self):
        '''Call the evaluation generator popup for the selected users.'''
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            return ''
        delivery_view = self.env.ref(
            'odoo_hr_evaluation_form.form_evaluation_generator')
        return {'name': _('Generate Evaluations'),
                'res_model': 'evaluation.generator',
                'view_mode': 'form',
                'view_id': delivery_view.id,
                'context': self.env.context,
                'target': 'new',
                'type': 'ir.actions.act_window'}

    @api.depends()
    def _appraisal_count_custom(self):
        Evaluation = self.env['hr.evaluation.interview']
        for employee in self:
            user_count = Evaluation.search_count(
                [('user_to_review_id', '=', employee.id)])
            employee.appraisal_count = user_count

    evaluation_plan_id_custom = fields.Many2one('hr_evaluation.plan', string='Appraisal Plan')
    evaluation_date_custom = fields.Date(string='Next Appraisal Date',
                                  help="The date of the next appraisal is computed by the appraisal plan's dates (first appraisal + periodicity).")
    _appraisal_count_custom = fields.Integer(compute='_appraisal_count_custom',
                                     string='Appraisal Interviews')


class HrEmployeePublic(models.Model):
    _inherit = "hr.employee.public"

    evaluation_plan_id_custom = fields.Many2one(
        'hr_evaluation.plan',
        related="employee_id.evaluation_plan_id_custom",
        readonly=True
    )
    evaluation_date_custom = fields.Date(
        readonly=True,
        related="employee_id.evaluation_date_custom"
    )
