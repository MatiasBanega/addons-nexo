# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError


class CompetenciesObjectives(models.Model):
    _name = 'competencies.objectives'
    _description = 'Competencies Objectives'
    _rec_name = 'competences_objectives_name'

    name = fields.Html(
        'Name',
        required=True,
    )
    type = fields.Selection(
        selection=[
            ('competencies', 'Competencies'),
            ('objectives', 'Objectives'),
        ],
        string='Type',
        default='competencies',
        readonly = True,
        required=True,
    )
    competences_objectives_name = fields.Text(
        'Name',
        compute="_compute_competences_objectives_name",
        store=True,
    )
    active = fields.Boolean(
        'Active',
        default=True,
    )

    @api.depends('name')
    def _compute_competences_objectives_name(self):
        for rec in self:
            rec.competences_objectives_name
            if rec.name:
                rec.competences_objectives_name = tools.html2plaintext(rec.name)

    def unlink(self):
        raise UserError(_("You are not allowed to delete the configuration but you can archive it instead."))
        return super(CompetenciesObjectives, self).unlink()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

