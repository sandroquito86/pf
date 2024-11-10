# -*- coding: utf-8 -*-
# from odoo import http


# class Pf/pfPersonalizacion(http.Controller):
#     @http.route('/pf/pf_personalizacion/pf/pf_personalizacion', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pf/pf_personalizacion/pf/pf_personalizacion/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('pf/pf_personalizacion.listing', {
#             'root': '/pf/pf_personalizacion/pf/pf_personalizacion',
#             'objects': http.request.env['pf/pf_personalizacion.pf/pf_personalizacion'].search([]),
#         })

#     @http.route('/pf/pf_personalizacion/pf/pf_personalizacion/objects/<model("pf/pf_personalizacion.pf/pf_personalizacion"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pf/pf_personalizacion.object', {
#             'object': obj
#         })

