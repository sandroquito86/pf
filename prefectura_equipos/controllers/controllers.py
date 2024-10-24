# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


# class MantenimientoAssetControllers(http.Controller):
#     @http.route(['/prefectura_equipos/boton'], type='json',website=True, auth='public')
#     def get_boton(self, **kw):
#         asset = http.request.env['asset.asset'].sudo().search([('id','!=',0)])
#         p=[]        
#         for activo in asset:
#             n = {'name':activo.name,'id':activo.id}
#             p.append(n)
#         return p

#     @http.route('/gestion-mantenimiento/prefectura_equipos/gestion-mantenimiento/prefectura_equipos/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('gestion-mantenimiento/prefectura_equipos.listing', {
#             'root': '/gestion-mantenimiento/prefectura_equipos/gestion-mantenimiento/prefectura_equipos',
#             'objects': http.request.env['gestion-mantenimiento/prefectura_equipos.gestion-mantenimiento/prefectura_equipos'].search([]),
#         })

#     @http.route('/gestion-mantenimiento/prefectura_equipos/gestion-mantenimiento/prefectura_equipos/objects/<model("gestion-mantenimiento/prefectura_equipos.gestion-mantenimiento/prefectura_equipos"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('gestion-mantenimiento/prefectura_equipos.object', {
#             'object': obj
#         })
