from tracemalloc import start
from odoo import models,fields,api
from odoo.tools.misc import xlwt
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import json

class CBReport(models.TransientModel):
    _name = 'report.report_cb_report'

    project_ids = fields.Many2many('project.project',string='Project many2many')
    select_all_rec = fields.Boolean(string="Select All",default=False)
    deselect_all_rec = fields.Boolean(string="Deselect All",default=False)

    @api.model
    def default_get(self, default_fields):
        res = super(CBReport, self).default_get(default_fields)
        project = self.env['project.project'].search([])
        res.update({'project_ids':[(6, 0, project.ids)]})
        return res

    @api.onchange('select_all_rec')
    def select_project_records(self):
        if self.select_all_rec == True:
            self.deselect_all_rec = False
            for rec in self.project_ids:
                rec.report_wizard_bool = True

    @api.onchange('deselect_all_rec')
    def deselect_project_records(self):
        if self.deselect_all_rec == True:
            self.select_all_rec = False
            for rec in self.project_ids:
                rec.report_wizard_bool = False

    def generate_xlsx_report(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/project/excel_report',
            'target': 'self',
        }
