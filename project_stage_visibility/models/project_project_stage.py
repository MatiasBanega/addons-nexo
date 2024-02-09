from odoo import models, api

class ProjectProject(models.Model):
    _inherit = 'project.project'

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        user = self.env.user
        visibility = self.env['project.stage.visibility'].search([
            ('user_id', '=', user.id), ('invisible', '=', True)
        ])
        if len(visibility) > 0:
            args += [('stage_id', 'not in', visibility.mapped('stage_id').ids)]
        return super(ProjectProject, self).search(args, offset, limit, order, count)
    
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        # get the user and visibility
        user = self.env.user
        visibility = self.env['project.stage.visibility'].search([
            ('user_id', '=', user.id), ('invisible', '=', True)
        ])
        
        # add a new domain to exclude the invisible stages
        if visibility:
            domain.append(('stage_id', 'not in', visibility.mapped('stage_id').ids))
        
        # call the super method
        return super(ProjectProject, self).read_group(domain, fields, groupby, offset, limit, orderby, lazy)


class ProjectProjectStage(models.Model):
    _inherit = 'project.project.stage'

    def unlink(self):
        # Before deletion, find all visibility rules that are related to stages about to be deleted
        visibilities = self.env['project.stage.visibility'].search([('stage_id', 'in', self.ids)])

        # Iterate through visibility rules and remove the references to the stages about to be deleted
        for visibility in visibilities:
            visibility.stage_id = [(3, stage_id) for stage_id in self.ids]

        return super(ProjectProjectStage, self).unlink()


    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        user = self.env.user
        visibility = self.env['project.stage.visibility'].search([
            ('user_id', '=', user.id), ('invisible', '=', True)
        ])
        if len(visibility) > 0:
            args += [('id', 'not in', visibility.mapped('stage_id').ids)]
        return super(ProjectProjectStage, self).search(args, offset, limit, order, count)

