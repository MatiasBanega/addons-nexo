# -*- coding: utf-8 -*-

from odoo import models


class mail_thread(models.AbstractModel):
    """
    Overwrite to make sure attatchments updated through emails would have correct folder
    We should not do that in 'write' since it would be recursive update
    """
    _inherit = 'mail.thread'

    def _message_post_process_attachments(self, attachments, attachment_ids, message_values):
        """
        Overwrite to pass 'cloud_key' to attachments

        Returns:
         * list of dicts per each message in the format for web client
        """
        if attachment_ids:
            model = message_values['model']
            res_id = message_values['res_id']
            filtered_attachment_ids = self.env['ir.attachment'].sudo().browse(attachment_ids).filtered(
                lambda a: a.res_model == 'mail.compose.message' and a.create_uid.id == self._uid
            )
            if filtered_attachment_ids:
                values = {'res_model': model, 'res_id': res_id}
                res_domain = [("res_id", "=", res_id), ("res_model", "=", model)]
                folder_id = self.sudo().with_context(active_test=False).env["clouds.folder"].search(res_domain, limit=1)     
                if folder_id:
                    values.update({"clouds_folder_id": folder_id.id})
                filtered_attachment_ids.write(values)            
        return super(mail_thread, self)._message_post_process_attachments(
            attachments=attachments, attachment_ids=attachment_ids, message_values=message_values,
        )
