from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class IrCron(models.Model):
    _name = 'ir.cron'
    _inherit = 'ir.cron'

    table_ids = fields.One2many('izi.table', 'cron_id', string='Tables')
    analytic = fields.Boolean('For Analytic Purpose')
