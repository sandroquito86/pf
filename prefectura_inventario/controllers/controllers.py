# -*- coding: utf-8 -*-
# from odoo import http


# class Prefectura/prefecturaInventario(http.Controller):
#     @http.route('/prefectura/prefectura_inventario/prefectura/prefectura_inventario', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/prefectura/prefectura_inventario/prefectura/prefectura_inventario/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('prefectura/prefectura_inventario.listing', {
#             'root': '/prefectura/prefectura_inventario/prefectura/prefectura_inventario',
#             'objects': http.request.env['prefectura/prefectura_inventario.prefectura/prefectura_inventario'].search([]),
#         })

#     @http.route('/prefectura/prefectura_inventario/prefectura/prefectura_inventario/objects/<model("prefectura/prefectura_inventario.prefectura/prefectura_inventario"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('prefectura/prefectura_inventario.object', {
#             'object': obj
#         })

