# -*- coding: utf-8 -*-

import base64

from odoo import _, api, fields, models
from odoo.exceptions import UserError


FORBIDDENSYMBOLS = ['~', '#', '&', ':', '{', '}', '*', '?', '"', "'", '<', '>', '|', '+', '%', '!', '@', '\\', '/']
SPECIAL_MIMETYPES = [
    "application/vnd.google-apps.spreadsheet", "application/vnd.google-apps.document",
    "application/vnd.google-apps.presentation",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
]
FOLDER_MIMETYPES = ["application/vnd.google-apps.folder", "dir"]
NOT_SYNCED_MIMETYPES = ["text/html", "text/css", "text/javascript", "application/javascript", "text/xml", 
                        "application/xml"]
MAX_NAME_LEN = 180

def check_allowed_mimetypes(mimetype):
    """
    This mimetype is required only for 'special' mimetypes. Standard ones are defined by Odoo
    """
    available_mimetypes = SPECIAL_MIMETYPES + FOLDER_MIMETYPES
    if not mimetype or mimetype not in (SPECIAL_MIMETYPES + FOLDER_MIMETYPES):
        mimetype = False
    elif mimetype in FOLDER_MIMETYPES:
        mimetype = "special_cloud_folder"
    return mimetype

class ir_attachment(models.Model):
    """
    Overwritting to prepare method for cloud api methods

    When use:
     * Introduce to-implement methods (in the bottom)
     * Try to optimize cron_synchronize_attachments_backward if sth like 'track changes' method exists in a client

    Extra info:
     * in comparison to folders we do not remove illegal characters and do not make titles unique assuming that
       it would be done in queue, since:
        (a) it is very bad for performace while installing the app and during any attachment upload
        (b) we do not assume that backward renaming would make any change in Odoo
    """
    _inherit = "ir.attachment"

    @api.depends('store_fname', 'db_datas')
    def _compute_raw(self):
        """
        Fully re-write core function to pass cloud_key to file-read
        """
        for attach in self:
            if attach.type == "url" and attach.cloud_key:
                try:
                    attach.raw = self._file_read(attach.store_fname, attach)
                except Exception as er:
                    attach.raw = False
            elif attach.store_fname:
                attach.raw = attach._file_read(attach.store_fname)
            else:
                attach.raw = attach.db_datas

    def _inverse_datas(self):
        """
        Overwrite to avoid writing on cloud datas into Odoo
        """
        for attach in self:
            if not attach.cloud_key:
                super(ir_attachment, attach)._inverse_datas()

    def _inverse_raw(self):
        """
        Overwrite to avoid writing on cloud datas into Odoo
        """
        for attach in self:
            if not attach.cloud_key:
                super(ir_attachment, attach)._inverse_raw()

    for_delete = fields.Boolean(default=False, string="Marked for delete")
    active = fields.Boolean(string="Active", default=True)
    clouds_folder_id = fields.Many2one(
        "clouds.folder", 
        string="Folder",
        index=True,
        ondelete="set null",
    )
    sync_cloud_folder_id = fields.Many2one("clouds.folder", string="Folder used for sync")
    sync_client_id = fields.Many2one("clouds.client", string="Client used for sync")
    cloud_key = fields.Char(string="Cloud key", copy=False)
    # introduced for inheritance purposes to filter not-syncing attachments
    handler = fields.Char(string="Handler")

    ####################################################################################################################
    ##################################   CORE methods   ################################################################
    ####################################################################################################################
    @api.model
    def check(self, mode, values=None):
        """
        Re-write to pass context for clouds.folder reference
        """
        super(ir_attachment, self.with_context(ir_attachment_security=True)).check(mode=mode, values=values)

    def read(self, fields=None, load='_classic_read'):
        """
        Overwrite to add fields which are required for updated js interface
        """
        if fields and 'for_delete' not in fields:
            fields = fields + ['for_delete']
        if fields and "cloud_key" not in fields:
            # to have in widgets
            fields = fields + ['cloud_key']
        if fields and "url" not in fields:
            # to have in widgets
            fields = fields + ['url']
        result = super(ir_attachment, self).read(fields=fields, load=load)
        return result

    @api.model_create_multi
    def create(self, vals_list):
        """
        Re-write to make sure that if an attachment has a linked record it would immediately linked to its folder

        Extra info:
         * attachments with res_model, but without res_id are do not pass security checks > so, we write cloud_folder
           own id and its model name
         * here we also check the very special case - of attachment linked to document.document, since such attachment
           relates not to a worskpace, but a document itself. So, we should not change its res_model & res_id
        """
        for values in vals_list:
            if values.get("clouds_folder_id"):
                folder_id = self.sudo().env["clouds.folder"].browse(values.get("clouds_folder_id")).exists()
                if folder_id and (folder_id.res_model != "documents.folder" or not folder_id.res_id):
                    if folder_id.res_id: 
                        values.update({"res_model": folder_id.res_model, "res_id": folder_id.res_id})
                    else:
                        values.update({"res_model": "clouds.folder", "res_id": folder_id.id})
            elif values.get("res_id") and values.get("res_model"):
                res_domain = [
                    ("res_id", "=", values.get("res_id")), 
                    ("res_model", "=", values.get("res_model")),
                ]
                folder_id = self.sudo().with_context(active_test=False).env["clouds.folder"].search(res_domain, limit=1)     
                if folder_id:
                    values.update({"clouds_folder_id": folder_id.id})
        return super(ir_attachment, self).create(vals_list)

    def write(self, vals):
        """
        Re-write to change attachment values if folder is changed

        Extra info:
         * context args 'no_folder_update' should be passed each time a brand new (not commited) clouds folder 
           is created and then linked to attachment (exactly through auto folders' preparation)
         * here we also check the very special case - of attachment linked to document.document, since such attachment
           relates not to a worskpace, but a document itself. So, we should not change its res_model & res_id
         * here we do not check for res_id, res_model changes, since it actually happen only for mail attachments 
           (see mail_thread), while here it would trigger recursive issues  
        """
        folder_id = False
        if not self._context.get("no_folder_update") and vals.get("clouds_folder_id") is not None:
            vals.update({"res_model": False, "res_id": 0})
            if vals.get("clouds_folder_id"):
                folder_id = self.sudo().env["clouds.folder"].browse(vals.get("clouds_folder_id")).exists()
                if folder_id and (folder_id.res_model != "documents.folder" or not folder_id.res_id):
                    if folder_id.res_id: 
                        vals.update({"res_model": folder_id.res_model, "res_id": folder_id.res_id})
                    else:
                        vals.update({"res_model": "clouds.folder", "res_id": folder_id.id})
        return super(ir_attachment, self).write(vals)

    def unlink(self):
        """
        Overwite unlink to guarantee that a synced attachment would be deleted only after deletion is done per client
        Normal not synced attachment (with cloud_key) are deleted right there

        Synced attachments are deleted as 2 steps-process:
         1. Firstly mark for delete 
         2. During the next unlink - delete an item (might happen only explicitly)

        Extra info:
         * we make extra check for rights, since 'writing' for_delete is also unlink, not 'write'
        """
        if not self:
            return True
        self.check('unlink')
        for_delete = self.filtered(lambda at: at.for_delete or not at.cloud_key)
        mark_for_delete = self - for_delete
        mark_for_delete.write({"for_delete": True, "active": False})
        result = super(ir_attachment, for_delete).unlink()
        return result

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        """
        Re-write to pass context for clouds.folder reference
        """
        return super(ir_attachment, self.with_context(ir_attachment_security=True))._search(
            args=args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid,
        )        

    def copy(self, default=None):
        """
        Overwrite not allow to copy attachments marked to delete
        """
        self.check('write')
        if self.for_delete:
            raise UserError(_("Can't copy attachments marked to delete"))
        if self.cloud_key:
            raise UserError(_("Can't copy synced attachments"))
        return super(ir_attachment, self).copy(default)

    @api.model
    def _file_read(self, fname, attach_cloud_id=False):
        """
        Rewrite to read files from Cloud client

        Extra Args:
         * attach_cloud_id - ir.attachment object

        Extra Methods:
         * _return_client_context of clouds.client
         * _upload_attachment_from_cloud
        """
        if not attach_cloud_id:
            r = super(ir_attachment, self)._file_read(fname=fname)
        else:
            r = attach_cloud_id.sudo()._upload_attachment_from_cloud()
            if not r:
                raise UserError(_("Binary content cannot be retrieved from clouds")) 
        return r      

    def action_return_all_pages_ids(self, domain):
        """
        The method to search attachments by js domain

        Returns:
         *  list of all selected attachments
        """
        all_attachments = set(self.ids + self.search(domain).ids)
        return list(all_attachments)

    def _upload_attachment_from_cloud(self):
        """
        Method to upload attachment from cloud

        Methods:
         * _upload_attachment_from_cloud of clouds.client
         * _return_specific_client_context of clouds.client

        Returns:
         * Binary File
         * False if method failed

        Extra info:
         * Expected singleton
        """
        ctx = self._context.copy()
        cfolder = self.sync_cloud_folder_id or self.clouds_folder_id
        cclient = cfolder.client_id 
        if "cclients" not in ctx.keys():
            new_ctx = cclient.sudo()._return_specific_client_context()
            ctx.update(new_ctx)
        self = self.with_context(ctx)
        cfolder = self.sync_cloud_folder_id or self.clouds_folder_id
        cclient = cfolder.client_id 
        return cclient._upload_attachment_from_cloud(cfolder, self, self.cloud_key, {})

    def action_donwload_cloud_file(self):
        """
        The method to retrieve content from clouds

        Returns:
         * action dict

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        return {
            "type": 'ir.actions.act_url',
            "target": 'new',
            "url": "web/content/{}?download=true".format(self.id),
        }

    ####################################################################################################################
    ##################################   SYNC-related helpers ##########################################################
    ####################################################################################################################
    def _filter_non_synced_attachments(self):
        """
        The method to filter system attachments

        Retunrs:
         * ir.attachment recordset
        """
        mime_types = NOT_SYNCED_MIMETYPES
        mime_types_conf = self.env['ir.config_parameter'].sudo().get_param('cloud_base.notsynced_mimetypes', "")
        if mime_types_conf:
            mime_types += mime_types_conf.split(",")
        attachments = self
        for attachment in self:
            if attachment.handler or attachment.mimetype in mime_types  \
                    or (attachment.type == "url" and not attachment.cloud_key) \
                    or attachment.name.startswith('/') or (attachment.url and attachment.url.startswith('/')) \
                    or attachment.res_field:
                attachments -= attachment
        return attachments
    
    @api.model
    def _remove_illegal_characters(self, s, safe_name="NOT CORRECT NAME", check_extension=False):
        """
        The method to replace not safe file system characters

        Args:
         * s - string
         * safe_name - what should be used instead of name, if method results in empty string
         * check_extension - bool - whether in case of big name size, we should consider extension not to be cut

        Returns:
         * s - string
        
        Extra info:
         * The method is not global to use in all Clients
         * We cut the item name if it is has too long name; since we cannot control path length, we apply
           each time shortening: 
           ** Dropbox - 255 for each item name (not full path): https://github.com/dropbox/dropbox-sdk-java/issues/229
           ** Owncloud - seems to be some 227 symbols (experimentally, but not totally sure)
           OS filesystem might have also their own limits (ubuntu has default config for 255 symbols); Windows
           block 260bytes paths
           So, with adding tolerance it's decided to cut 180-long items
        """
        def find_index_dot(s_list): 
            """
            The method to find 

            Args:
             * s_list - str
            
            Returns:
             * int - number of the first dot in string
            """
            start = 0
            for symbol in s_list:
                if symbol in [".", " "]:
                    start += 1
                else:
                    break 
            return start 
        # to make sure item name is not empty 
        s = s or safe_name
        # to replace dangerous symboles from item name
        for symbol in FORBIDDENSYMBOLS:
            s = s.replace(symbol, "-") 
        # remove space and dots at the beginning and at the end if any
        start = find_index_dot(s)
        end = find_index_dot(reversed(s))
        if start:
            s = s[start:]
        if end:
            s = s[:-end]      
        # final checks        
        if len(s) > MAX_NAME_LEN:
            # cut too big names
            if not check_extension:
                # if not extension, just remove the last symbols
                s = s[:MAX_NAME_LEN]
            else:
                last_dot = s.rfind(".")
                if last_dot == -1 or (len(s)-last_dot > 50):
                    # no dot or extension is too big
                    s = s[:MAX_NAME_LEN]
                else:
                    s1 = s[:last_dot]
                    s2 = s[last_dot:]
                    s1 = s1[:MAX_NAME_LEN-len(s2)]
                    s = s1 + s2
        else:
            # make sure final element is not empty
            s = s or safe_name
        return s

    ####################################################################################################################
    ##################################   INTERFACE methods   ###########################################################
    ####################################################################################################################
    def open_cloud_link(self):
        """
        The method to get action for opening cloud link
        """
        self = self.sudo()
        res = False
        if self.url:
            res = {
                'name': _('Open in clouds'),
                'res_model': 'ir.actions.act_url',
                'type': 'ir.actions.act_url',
                'target': 'new',
                'url': self.url,
            }
        return res        

    def return_selected_attachments(self):
        """
        The method to return selected attachments

        Returns:
          * list of dict of attachments values requried for mass operations
        """
        self = self.with_context(lang=self.env.user.lang)
        attachments = []
        for attachment in self:
            attachments.append({"id": attachment.id, "name": attachment.name})
        return attachments

    @api.model
    def return_js_upload_form(self):
        """
        The method to open new attachment form to create a new one for defaults js tree 
        """
        view_id = self.sudo().env.ref('cloud_base.ir_attachment_view_form_simple_js_upload').id
        return view_id        
