# -*- coding: utf-8 -*-
# from odoo import http


# class PfBase(http.Controller):
#     @http.route('/prefectura_base/prefectura_base', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/prefectura_base/prefectura_base/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('prefectura_base.listing', {
#             'root': '/prefectura_base/prefectura_base',
#             'objects': http.request.env['prefectura_base.prefectura_base'].search([]),
#         })

#     @http.route('/prefectura_base/prefectura_base/objects/<model("prefectura_base.prefectura_base"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('prefectura_base.object', {
#             'object': obj
#         })

