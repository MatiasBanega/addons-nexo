# -*- coding: utf-8 -*-
# from odoo import http


# class Correcciones(http.Controller):
#     @http.route('/correcciones/correcciones', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/correcciones/correcciones/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('correcciones.listing', {
#             'root': '/correcciones/correcciones',
#             'objects': http.request.env['correcciones.correcciones'].search([]),
#         })

#     @http.route('/correcciones/correcciones/objects/<model("correcciones.correcciones"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('correcciones.object', {
#             'object': obj
#         })
