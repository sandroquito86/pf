# -*- coding: utf-8 -*-
# from odoo import http


# class Pf/manzanaConvoy(http.Controller):
#     @http.route('/pf/manzana_convoy/pf/manzana_convoy', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pf/manzana_convoy/pf/manzana_convoy/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('pf/manzana_convoy.listing', {
#             'root': '/pf/manzana_convoy/pf/manzana_convoy',
#             'objects': http.request.env['pf/manzana_convoy.pf/manzana_convoy'].search([]),
#         })

#     @http.route('/pf/manzana_convoy/pf/manzana_convoy/objects/<model("pf/manzana_convoy.pf/manzana_convoy"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pf/manzana_convoy.object', {
#             'object': obj
#         })

