# -*- coding: utf-8 -*-
# from odoo import http


# class ManzanaEjecucion(http.Controller):
#     @http.route('/manzana_ejecucion/manzana_ejecucion', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/manzana_ejecucion/manzana_ejecucion/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('manzana_ejecucion.listing', {
#             'root': '/manzana_ejecucion/manzana_ejecucion',
#             'objects': http.request.env['manzana_ejecucion.manzana_ejecucion'].search([]),
#         })

#     @http.route('/manzana_ejecucion/manzana_ejecucion/objects/<model("manzana_ejecucion.manzana_ejecucion"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('manzana_ejecucion.object', {
#             'object': obj
#         })

