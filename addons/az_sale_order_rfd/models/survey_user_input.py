from odoo import models, fields

# below fields are created in studio and added here so we can use in code (not added in views under this module)

class SurveyUserInput(models.Model):
    _inherit = "survey.user_input"
    
    x_project = fields.Many2one("project.project")
    
class Survey(models.Model):
    _inherit = "survey.survey"
    
    def _create_answer(self, user=False, partner=False, email=False, test_entry=False, check_attempts=True, **additional_vals):
        if self.env.context.get("az_rfd_start_survey", False) and self.env.context.get("az_rfd_survey_user", False) and self.env.context.get("rfd_id", False):
            rfd_id = self.env["request.for.delivery"].browse(self.env.context.get("rfd_id", []))
            if rfd_id:
                partner = self.env.context.get("az_rfd_survey_user", self.env["res.users"]).partner_id
                email = partner.email
                user = False
                additional_vals['x_project'] = rfd_id.sale_order_id.project_id.id
        return super()._create_answer(user=user, partner=partner, email=email, test_entry=test_entry, check_attempts=check_attempts, **additional_vals)

class ResCompany(models.Model):
    _inherit = "res.company"
    
    x_agency_survey = fields.Many2one("survey.survey")