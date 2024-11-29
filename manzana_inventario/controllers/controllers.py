# -*- coding: utf-8 -*-
# from odoo import http


# class Prefectura/manzanaInventario(http.Controller):
#     @http.route('/prefectura/manzana_inventario/prefectura/manzana_inventario', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/prefectura/manzana_inventario/prefectura/manzana_inventario/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('prefectura/manzana_inventario.listing', {
#             'root': '/prefectura/manzana_inventario/prefectura/manzana_inventario',
#             'objects': http.request.env['prefectura/manzana_inventario.prefectura/manzana_inventario'].search([]),
#         })

#     @http.route('/prefectura/manzana_inventario/prefectura/manzana_inventario/objects/<model("prefectura/manzana_inventario.prefectura/manzana_inventario"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('prefectura/manzana_inventario.object', {
#             'object': obj
#         })

