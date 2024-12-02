# -*- coding: utf-8 -*-
# from odoo import http


# class GuayasIntegra(http.Controller):
#     @http.route('/guayas_integra/guayas_integra', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/guayas_integra/guayas_integra/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('guayas_integra.listing', {
#             'root': '/guayas_integra/guayas_integra',
#             'objects': http.request.env['guayas_integra.guayas_integra'].search([]),
#         })

#     @http.route('/guayas_integra/guayas_integra/objects/<model("guayas_integra.guayas_integra"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('guayas_integra.object', {
#             'object': obj
#         })

