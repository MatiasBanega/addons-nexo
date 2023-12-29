from odoo import models, api


class Notification(models.Model):
    _name = "notification.nexo"
    _description = "Notification Nexo"

    def action_notification(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Registrar marcación de salida',
                'message': 'Recordá registrar tu marcación de salida',
                'type': 'danger',
                'sticky': False
            }
        }