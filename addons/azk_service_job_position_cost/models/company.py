from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"
    
    designation_cost_calculate = fields.Selection([('highest','Highest Designation Cost'),('average','Average Designation Cost'),('lowest','Lower Designation Cost')],default="highest", string="Designation Cost Calculation")