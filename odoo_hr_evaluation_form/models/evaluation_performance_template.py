# -*- coding: utf-8 -*-

from odoo import models, fields


class EvaluationTemplate(models.Model):
    _name = 'evalution.competencies.objectives.template'
    _description = 'Evaluation Question Template'

    name = fields.Char(
        'Name',
        required=True,
    )
    performance_introduction = fields.Text(
        'Introduction'    
    )
    competencies_line_ids = fields.One2many(
        'competencies.objectives.template.line',
        'competencies_id',
        copy = True,
    )
    objectives_line_ids = fields.One2many(
        'competencies.objectives.template.line',
        'objectives_id',
        copy = True,
    )
    active = fields.Boolean(
        'Active',
        default=True,
    )

    def unlink(self):
        raise UserError(_("You are not allowed to delete the configuration but you can archive it instead."))
        return super(CompetenciesObjectives, self).unlink()


class EvaluationTemplate(models.Model):
    _name = 'competencies.objectives.template.line'
    _description = 'Evaluation Question Template Lines'
    _rec_name = 'competencies_objectives_id'

    competencies_objectives_id = fields.Many2one(
        'competencies.objectives',
        required=True,
    )
    competencies_id = fields.Many2one(
        'evalution.competencies.objectives.template',
        'Template'
    )
    objectives_id = fields.Many2one(
        'evalution.competencies.objectives.template',
        'Template'
    )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
