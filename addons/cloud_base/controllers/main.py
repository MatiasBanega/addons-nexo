# -*- coding: utf-8 -*-

import io
import base64
import json
import zipfile

from odoo import _, fields, http
from odoo.http import content_disposition, request


class cloudFiles(http.Controller):
    """
    Controller to manage attachments operations in file manager
    """
    @http.route('/cloud_base/upload_attachment', type='http', methods=['POST'], auth="user")
    def upload_to_file_manager(self, ufile, **kwargs):
        """
        The method to create folder-related attachment based on uploaded file
        """
        if kwargs.get("clouds_folder_id") == "0" or not kwargs.get("clouds_folder_id"):
            result = {'error': _("Please select a folder for uploaded files")}
        else:
            files = request.httprequest.files.getlist('ufile')
            for ufile in files:
                try:
                    mimetype = ufile.content_type
                    request.env["ir.attachment"].create({
                        "name": ufile.filename,
                        "clouds_folder_id": int(kwargs.get("clouds_folder_id")),
                        "mimetype": mimetype,
                        "datas": base64.encodebytes(ufile.read()),
                    })
                    result = {"success": _("All files uploaded")}
                except Exception as e:
                    result = {"error": str(e)}
        return json.dumps(result)

    @http.route(['/cloud_base/multiupload/<string:attachments>'], type='http', auth='user')
    def multi_download_file_manager(self, attachments, **kwargs):
        """
        The method to download multiple files as a zip archive

        Methods:
         * _binary_ir_attachment_redirect_content if ir.http
         * _binary_record_content of ir.http
        """
        attachment_ids = request.env["ir.attachment"]
        if attachments:
            attachment_ids = attachments.split(",")
            attachment_ids = [int(art) for art in attachment_ids]
            attachment_ids = request.env["ir.attachment"].browse(attachment_ids).exists()
        stream = io.BytesIO()
        try:
            with zipfile.ZipFile(stream, 'w') as z_archive:
                for attachment_id in attachment_ids:
                    if attachment_id.type == "binary":
                        st, content, filename, mt, fh = request.env['ir.http']._binary_record_content(
                            attachment_id, field='datas', filename=None, filename_field='name',
                            default_mimetype='application/octet-stream') 
                    elif (attachment_id.type == "url" and attachment_id.cloud_key):
                        st, content, filename, mt, fh = request.env['ir.http']._binary_ir_attachment_redirect_content(
                            attachment_id, default_mimetype='application/octet-stream'
                        )                                           
                    if not content:
                        continue 
                    z_archive.writestr(filename, base64.b64decode(content), compress_type=zipfile.ZIP_DEFLATED)
        except zipfile.BadZipfile:
            pass
        content = stream.getvalue()
        archive_title = kwargs.get("archive_name") or "{}".format(fields.Datetime.now())
        headers = [
            ('Content-Type', 'zip'),
            ('X-Content-Type-Options', 'nosniff'),
            ('Content-Length', len(content)),
            ('Content-Disposition', content_disposition("odoo_{}.zip".format(archive_title)))
        ]
        return request.make_response(content, headers)

    @http.route(['/cloud_base/folder_upload/<model("clouds.folder"):folder_id>'], type='http', auth='user')
    def folder_download_file_manager(self, folder_id, **kwargs):
        """
        The method to prepare cloud folder attachments for downloading

        Methods:
         * multi_download_file_manager
        """
        attachment_ids = request.env["ir.attachment"].search([("clouds_folder_id", "=", folder_id.id)]).ids
        att_param = ','.join(str(at) for at in attachment_ids)
        return self.multi_download_file_manager(att_param, archive_name=folder_id.name)

    @http.route(['/cloud_base/export_logs'], type='http', auth='user')
    def cloud_base_export_logs(self, search_params):
        """
        The method to prepare txt files with logs

        Methods:
         * _prepare_txt_logs
        """
        search_params = json.loads(search_params)
        content = request.env["clouds.log"]._prepare_txt_logs(
            search_params.get("search_domain"), search_params.get("selected_clients"),
        ).encode('utf-8')
        headers = [
            ('Content-Type', 'zip'),
            ('X-Content-Type-Options', 'nosniff'),
            ('Content-Length', len(content)),
            ('Content-Disposition', content_disposition("cloud_base_{}.logs".format(fields.Datetime.now())))
        ]
        return request.make_response(content, headers)
