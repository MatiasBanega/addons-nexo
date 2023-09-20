# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class subtask_wizard(models.Model):
    _name = 'subtask.wizard'
    _description = 'Subtask Wizard'

    subtask_lines = fields.One2many('project.task', 'wiz_id', string="Task Line")

    def create_subtask(self):
        project_id = self.env['project.task'].browse(self._context.get('active_id'))
        for task in self.subtask_lines:
            task.task_parent_id = self._context.get('active_id')
            task.description = task.des
            task.stage_id = 1
            task.project_id = project_id.project_id.id
        return True


class ProjectTask(models.Model):
    _inherit = "project.task"

    wiz_id = fields.Many2one('subtask.wizard', string="Wiz Parent Id")
    task_parent_id = fields.Many2one('project.task', string="Parent Id")
    subtask_ids = fields.One2many('project.task', 'task_parent_id', string="Subtask")
    des = fields.Char('Descriptions')
