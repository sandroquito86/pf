# -*- coding: utf-8 -*-
# from odoo import http


# class ManzanaDelCuidado(http.Controller):
#     @http.route('/manzana_de_cuidados/manzana_de_cuidados', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/manzana_de_cuidados/manzana_de_cuidados/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('manzana_de_cuidados.listing', {
#             'root': '/manzana_de_cuidados/manzana_de_cuidados',
#             'objects': http.request.env['manzana_de_cuidados.manzana_de_cuidados'].search([]),
#         })

#     @http.route('/manzana_de_cuidados/manzana_de_cuidados/objects/<model("manzana_de_cuidados.manzana_de_cuidados"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('manzana_de_cuidados.object', {
#             'object': obj
#         })

