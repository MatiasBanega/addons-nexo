from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"
    
    computed_fields_hourly_cost = fields.Many2many('ir.model.fields', string="Calculate Total Salary Based On" ,domain="[('ttype','in',['float','monetary']),('model','=','hr.contract')]")
    hourly_rate_factor =  fields.Float(string="Hourly Rate Factor", default="130")