# -*- coding: utf-8 -*-

from odoo import api, fields, models


class mass_attachment_update(models.TransientModel):
    """
    The model to keep attributes of mass update
    """
    _name = "mass.attachment.update"
    _description = "Update Attachments"

    attachments = fields.Char(string="Updated attachments")
    folder_id = fields.Many2one(
        "clouds.folder",
        string="Update folder",
    )

    @api.model
    def create(self, values):
        """
        Overwrite to trigger articles update

        Methods:
         * action_update_attachments

        Extra info:
         *  we do not use standard wizard buttons in the footer to use standard js forms
        """
        res = super(mass_attachment_update, self).create(values)
        res.action_update_attachments()
        return res

    def action_update_attachments(self):
        """
        The method update articles

        Methods:
         * _prepare_values

        Extra info:
         * we use articles char instead of m2m as ugly hack to avoid default m2m strange behaviour
         * Expected singleton
        """
        self.ensure_one()
        values = self._prepare_values()
        if values:
            attachment_ids = self.attachments.split(",")
            attachment_ids = [int(art) for art in attachment_ids]
            attachment_ids = self.env["ir.attachment"].browse(attachment_ids)
            attachment_ids.write(values)

    def _prepare_values(self):
        """
        The method to prepare values based on wizard fields

        Returns:
         * dict of values

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        values = {}
        if self.folder_id:
            values.update({"clouds_folder_id": self.folder_id.id})
        return values
