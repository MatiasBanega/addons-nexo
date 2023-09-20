from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class SweepWizard(models.TransientModel):

    _name = 'sweep.process.wizard'

    # records_to_sweep = fields.Integer("No. of Records")
    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', default=fields.Date.today, required=True)

    @api.onchange('start_date', 'end_date')
    def onchange_sweep_dates(self):
        if self.start_date and self.end_date:
            if self.env.company.sweep_start_date != self.start_date:
                self.env.company.sweep_start_date = self.start_date
            if self.env.company.sweep_end_date != self.end_date:
                self.env.company.sweep_end_date = self.end_date

    def process_sweep_scheduler(self):
        logging.info("Hamza Ilyas ----> process_sweep_scheduler Clicked on wizard")
        self.env['account.move'].cron_sweep_entries()
        # scheduler = self.env['ir.cron'].search([('name', '=', 'Sweep Process')])
        # scheduler.method_direct_trigger()

