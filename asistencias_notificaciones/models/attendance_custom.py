from odoo import models, fields, api, _


class AsistenciaNotificacion(models.Model):
    _name = 'asistencia.notificacion'

    def popupNotification(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Recordatorio'),
                'message': 'Recorda Marcar la salida',
                'sticky': True
            }
        }

    # def popupNotification(self):
    #     self.env['bus.bus']._sendone(self.env.user.partner_id,
    #                                  "simple_notification",
    #                                  {
    #                                      "title": "Recordatorio",
    #                                      "message": "Recorda marcar tu salida en el modulo de asistencias",
    #                                      "sticky": True
    #                                  })
    #     return True


        # Importa las clases y métodos necesarios
        # Encuentra los usuarios que deben recibir notificaciones (puedes filtrar por roles, departamentos, etc.)
        # users_to_notify = self.env['res.users'].search([])  # Filtra según tus criterios

        # Envía las notificaciones a los usuarios
        # for user in users_to_notify:
            # message = "Recuerda marcar tu fichada de asistencia."
            # self.env['hr_attendance'].create({
            #     'user_id': user.id,
            #     'message': message,
            #     'hora_envio': fields.Datetime.now(),
            # })

