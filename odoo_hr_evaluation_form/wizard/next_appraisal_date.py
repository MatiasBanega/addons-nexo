 # -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt. Ltd. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, _
import time

class CreateAppraisalDate(models.TransientModel):
    _name = "create.appraisal.date"
    _description= 'Create Appraisal Date'

    
    evaluation_date = fields.Date(
        string='Next Appraisal Date',
        help="The date of the next appraisal is computed by the appraisal plan's dates (first appraisal + periodicity)."
    )

    def action_next_appraisal_date(self):
        evaluation_id = self.env['hr_evaluation.evaluation'].browse(self._context.get('active_ids'))
        evaluation_id.write({'state': 'done', 'date_close': time.strftime('%Y-%m-%d')})
        evaluation_id.employee_id.evaluation_date_custom = self.evaluation_date
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
