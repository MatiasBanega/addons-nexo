from urllib.parse import urlencode, urljoin

from odoo import api, fields, models
from odoo.exceptions import ValidationError

class ProjectProject(models.Model):
    _inherit = "project.project"


    name = fields.Char(string="Name", store=True)

    @api.model
    def create(self, vals):
        res = super(ProjectProject, self).create(vals)
        body = "<p>A new project have been created for your attention click on the link above to review </p>"
        partner_ids = self.env.ref("libracycle_process_workflow.group_qac").mapped('users').mapped('partner_id').ids
        res.message_notify(partner_ids=partner_ids, body=body, subject=res.name, model=self._name, res_id=res.id)
        return res

    _sql_constraints = [
        ('project_uniq_name', 'unique(name)', "Project's name must be unique!"),
    ]