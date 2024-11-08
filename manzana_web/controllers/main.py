# -*- coding: utf-8 -*-


from odoo import http
from odoo.http import request
from datetime import datetime, time, timedelta, time
from functools import reduce
import base64
import json
import logging
import traceback

_logger = logging.getLogger(__name__)




class BeneficiarioController(http.Controller):
    @http.route(['/solicitud/beneficiario'], type='http', auth='public', website=True)
    def solicitud_beneficiario(self, **kw):
        # Primero, veamos todos los programas
        modulo = request.env.ref('prefectura_base.modulo_2')
        programas_filtrados = request.env['pf.programas'].sudo().search([])

        return request.render('manzana_web.solicitud_beneficiario_template', {
            'programas': programas_filtrados
        })
    

    @http.route('/solicitud/beneficiario/submit', type='http', auth='public', website=True, methods=['POST'])
    def beneficiario_submit(self, **post):
        try:
            _logger.info("Datos recibidos: %s", post)
            
            # Validar campos requeridos
            required_fields = [
                'apellido_paterno', 'apellido_materno', 'primer_nombre',
                'tipo_documento', 'numero_documento', 'fecha_nacimiento',
                'telefono', 'email', 'programa_id'
            ]
            
            # Verificar campos requeridos
            missing_fields = [field for field in required_fields if not post.get(field)]
            if missing_fields:
                return json.dumps({
                    'success': False,
                    'error': _('Los siguientes campos son requeridos: %s') % ', '.join(missing_fields)
                })
            
            # Preparar valores para crear el registro
            vals = {
                'apellido_paterno': post.get('apellido_paterno'),
                'apellido_materno': post.get('apellido_materno'),
                'primer_nombre': post.get('primer_nombre'),
                'segundo_nombre': post.get('segundo_nombre'),
                'tipo_documento': post.get('tipo_documento'),
                'numero_documento': post.get('numero_documento'),
                'fecha_nacimiento': post.get('fecha_nacimiento'),
                'telefono': post.get('telefono'),
                'email': post.get('email'),
                'programa_id': int(post.get('programa_id')),
                'state': 'submitted',
            }
            
            # Agregar país si está presente
            if post.get('pais_id'):
                vals['pais_id'] = int(post.get('pais_id'))
            
            _logger.info("Valores a crear: %s", vals)
            
            # Crear el registro
            solicitud = request.env['mz.solicitud.beneficiario'].sudo().create(vals)
            
            return request.redirect('/solicitud/beneficiario/gracias/%s' % solicitud.id)
            
        except Exception as e:
            _logger.error("Error al procesar la solicitud: %s", str(e), exc_info=True)
            return request.redirect('/solicitud/beneficiario?error=1')


    
    @http.route('/solicitud/beneficiario/gracias/<int:solicitud_id>', type='http', auth='public', website=True)
    def beneficiario_gracias(self, solicitud_id):
        solicitud = request.env['mz.solicitud.beneficiario'].sudo().browse(solicitud_id)
        if not solicitud.exists():
            return request.redirect('/solicitud/beneficiario')
            
        return request.render('manzana_web.solicitud_success_template', {
            'solicitud': solicitud
        })