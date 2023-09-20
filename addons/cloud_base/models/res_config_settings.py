# -*- coding: utf-8 -*-

from odoo import api, fields, models


class res_config_settings(models.TransientModel):
    """
    Cloud storage basic settings
    """
    _inherit = "res.config.settings"

    @api.onchange("cloud_log_days")
    def _onchange_cloud_log_days(self):
        """
        Onchange method for cloud_log_days
        """
        for config in self:
            if config.cloud_log_days < 3:
                config.cloud_log_days = 3

    notsynced_mimetypes = fields.Char(string="Not synced mimetypes", config_parameter="cloud_base.notsynced_mimetypes")
    cloud_log_days = fields.Integer(
        string="Logs storage period (days)", 
        config_parameter="cloud_base.cloud_log_days", 
        default=3,
    )
    module_google_drive_odoo = fields.Boolean(string="Google Drive Sync")
    module_onedrive = fields.Boolean(string="OneDrive / SharePoint Sync")
    module_owncloud_odoo = fields.Boolean(string="ownCloud / Nextcloud Sync") 
    module_dropbox = fields.Boolean(string="Dropbox Sync")       
    module_cloud_base_documents = fields.Boolean(string="Sync Enterprise Documents")     

    def action_test_prepare_folders(self):
        """
        The method to manually launch folders' preparation cron job
        
        Methods:
         * method_direct_trigger of ir.cron
        """
        cron_id = self.sudo().env.ref("cloud_base.cloud_base_prepare_folders")
        cron_id.method_direct_trigger()

    def action_test_sync_job(self):
        """
        The method to manually launch sync cron job
        
        Methods:
         * method_direct_trigger of ir.cron
        """
        cron_id = self.sudo().env.ref("cloud_base.cloud_base_run_prepare_queue")
        cron_id.method_direct_trigger()
