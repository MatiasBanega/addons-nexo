from odoo import models, fields
import uuid

class RFDUploadFile(models.TransientModel):
    _name = "upload.rfd.file.wizard"
    _description = "Upload RFD File"
    
    file = fields.Binary(required=True)
    file_name = fields.Char()
    comment = fields.Char()
    
    def upload_file(self):
        active_rfd = self._context.get('active_rfd', False)
        if active_rfd:
            delivery_file_id = self.env["request.for.delivery.file"].sudo().create({"delivery_id": active_rfd, 
                                                                                    "comment": self.comment
                                                                                     })
            attachment_id = self.env["ir.attachment"].sudo().create({"datas" : self.file,
                                                                    "res_model": "request.for.delivery.file",
                                                                    "res_id": delivery_file_id.id,
                                                                    "name": self.file_name,
                                                                    "access_token": str(uuid.uuid4())})
            delivery_file_id.sudo().file_id = attachment_id.id