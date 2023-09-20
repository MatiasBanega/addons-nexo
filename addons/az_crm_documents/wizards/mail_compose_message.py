from odoo import models, _


class ComposeMessage(models.TransientModel):
    _inherit = "mail.compose.message"
    
    def add_document(self):
        return {
                "name": _("Add from Documents App"),
                "type": "ir.actions.act_window",
                "view_mode": "form",
                "res_model": "add.document.to.mail.composer",
                "target": "new",
                "context" : { "mail_compose_message_id" : self.id,
                              "model_name" : self.model,
                              "model_id" : self.res_id
                            }
            }