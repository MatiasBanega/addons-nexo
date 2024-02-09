from odoo import models, fields

class ProjectStageVisibility(models.Model):
    _name = 'project.stage.visibility'
    _description = 'Project Stage Visibility'

    name = fields.Char(string='Name', required=True, help="Enter the name of this visibility rule.")
    user_id = fields.Many2many('res.users', string='Users', required=True, help="Select the users this rule applies to.")
    stage_id = fields.Many2many('project.project.stage', string='Stages', required=True, help="Select the stages this rule applies to.")
    invisible = fields.Boolean(string='Hide Stages', help="If checked, the selected stages will be hidden from the selected users.")

