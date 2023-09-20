# -*- coding: utf-8 -*-

from odoo import models


class mail_message(models.Model):
    """
    Overwrite to pass cloud key to message attachments
    """
    _inherit = 'mail.message'

    def message_format(self, format_reply=True):
        """
        Overwrite to pass 'cloud_key' to attachments

        Returns:
         * list of dicts per each message in the format for web client
        """
        message_values = super(mail_message, self).message_format(format_reply=format_reply)
        for mes_value in message_values:
            for attachment_id_dict in mes_value.get("attachment_ids"):
                attachment_id_dict.update({
                    "cloud_key": self.env["ir.attachment"].browse(attachment_id_dict.get("id")).cloud_key
                })
        return message_values
