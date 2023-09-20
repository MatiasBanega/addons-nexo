# -*- coding: utf-8 -*-

from odoo import _, models
from odoo.exceptions import ValidationError

SYNC_CRONS = ["cloud_base.cloud_base_prepare_folders", "cloud_base.cloud_base_run_prepare_queue"]
CRON_WARNING = _("""It is forbidden to make sync crons last less than 15 minutes or repeat missed sync crons.
Make also sure your Odoo server timeouts are configured for 900 seconds at least.""")


class ir_cron(models.AbstractModel):
    """
    Re-write to forbid manual changes of frequency
    """
    _inherit = 'ir.cron'

    def write(self, values):
        """
        Forbid changing frequency of sync crons
        """
        res = super(ir_cron, self).write(values)
        for sync_cron in SYNC_CRONS:    
            ch_cron = self.sudo().env.ref(sync_cron)
            if ch_cron in self:
                if ch_cron.doall or (ch_cron.interval_type == "minutes" and ch_cron.interval_number < 15):
                    raise ValidationError(CRON_WARNING)
        return res
