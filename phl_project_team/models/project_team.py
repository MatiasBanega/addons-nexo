from odoo import models, fields, api


class CrmTeamInherit(models.Model):

    _inherit = "crm.team"

    type_team = fields.Selection([("sale", "Sale"), ("project", "Project")], string="Type", default="sale")

    team_members = fields.Many2many(
        "res.users",
        "project_team_user_rel",
        "team_id",
        "uid",
        "Project Members",
        help="""Project's members are users who
                                     can have an access to the tasks related
                                     to this project.""",
    )


class PhlProjectProject(models.Model):

    _inherit = "project.project"

    members = fields.Many2many(
        "res.users",
        "project_user_rel",
        "project_id",
        "uid",
        "Project Members",
        help="""Project's
                               members are users who can have an access to
                               the tasks related to this project.""",
    )
    team_id = fields.Many2one("crm.team", string="Project Team", domain=[("type_team", "=", "project")])

    @api.model
    def create(self, vals):
        if vals.get("team_id"):
            team_recs = self.env["crm.team"].search(
                [("type_team", "=", "project"), ("id", "=", int(vals.get("team_id")))]
            )
            vals["members"] = [(6, 0, team_recs.team_members.ids)]
        res = super(PhlProjectProject, self).create(vals)
        if res:
            res._add_project_followers()
        return res

    def write(self, vals):
        update_member_list = False
        if vals.get("team_id"):
            team_id = vals.get("team_id", self.team_id.id)
            team_recs = self.env["crm.team"].search([("type_team", "=", "project"), ("id", "=", int(team_id))])
            if team_recs:
                update_member_list = True
                vals["members"] = [(6, 0, team_recs.team_members.ids)]
        res = super(PhlProjectProject, self).write(vals)
        if res:
            if update_member_list:
                self._add_project_followers()
        return res

    def _get_users_to_project_subscribe(self, project=False):
        partner_ids = self.env["res.partner"]
        project = project or self
        if project.user_id:
            partner_ids |= project.user_id.partner_id
        if project.members:
            partner_ids |= project.members.mapped("partner_id")
        return partner_ids

    def _add_project_followers(self):
        users = self._get_users_to_project_subscribe()
        self.message_subscribe(partner_ids=users.ids)

    @api.onchange("team_id")
    def get_team_members_rec(self):
        res = {}
        if self.team_id:
            self.members = []
            team_user_id = self.team_id.team_members.ids
            res["domain"] = {"user_id": [("id", "in", team_user_id)]}
            self.members = [(6, 0, [rec.id for rec in self.team_id.team_members])]
        return res
