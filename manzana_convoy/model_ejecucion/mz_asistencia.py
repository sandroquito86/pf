# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime
from datetime import date
from datetime import timedelta
from babel.dates import format_date
from datetime import datetime, timedelta

class ConvoyAsistenciaServicio(models.Model):
    _inherit = 'mz.asistencia_servicio'

   
     
    @api.model
    def get_view(self, view_id=None, view_type='form', context=None, toolbar=False, submenu=False, **kwargs):
        context = context or {}
        user = self.env.user
        if user.has_group('manzana_convoy.group_mz_convoy_prestador_servicio') or \
           user.has_group('manzana_convoy.group_mz_convoy_administrador'):
            # Vistas completas para usuarios con permisos
            if view_type == 'tree':
                view_id = self.env.ref('manzana_de_cuidados.view_asistencia_servicio_tree').id
        else:
            # Vistas limitadas para usuarios sin permisos
            if view_type == 'tree':
                view_id = self.env.ref('manzana_de_cuidados.view_asistencia_servicio_tree_limit').id

        return super().get_view(
            view_id=view_id, 
            view_type=view_type, 
            context=context, 
            toolbar=toolbar, 
            submenu=submenu,
            **kwargs
        )
   
    def _search(self, args, offset=0, limit=None, order=None, access_rights_uid=None):
        """
        Método _search personalizado para filtrar turnos cuando viene el contexto
        """
        args = args or []
        user = self.env.user
        # Evitar recursión usando un contexto especial
        if not self._context.get('disable_custom_search'):
            if self._context.get('filtrar_asistencia_convoy'):
                # Verificar grupos
                if user.has_group('manzana_convoy.group_mz_convoy_administrador'):
                    # Para administrador: ver registros del módulo 4
                    programa_ids = self.with_context(disable_custom_search=True).search([
                        ('programa_id.modulo_id', '=', 4)
                    ]).ids
                    base_args = [('id', 'in', programa_ids)]
                elif user.has_group('manzana_convoy.group_mz_convoy_coordinador'):
                    # Primero obtenemos los convoy donde es director
                    convoy_ids = self.env['mz.convoy'].search([
                        ('director_coordinador.user_id', '=', user.id),
                        ('programa_id.modulo_id', '=', 4)
                    ]).mapped('programa_id').ids
                    programa_ids = self.with_context(disable_custom_search=True).search([
                        ('programa_id', 'in', convoy_ids)
                    ]).ids
                    base_args = [('id', 'in', programa_ids)]
                elif user.has_group('manzana_convoy.group_mz_convoy_prestador_servicio'):
                    # Obtener convoyes en ejecución
                    convoy_ids = self.env['mz.convoy'].search([('state', '=', 'ejecutando')])                    
                    # Buscar asignaciones con el contexto correcto
                    asignaciones = self.env['mz.asignacion.servicio'].with_context(disable_custom_search=True).search([
                        ('convoy_id', 'in', convoy_ids.ids),
                        ('personal_ids', 'in', user.employee_id.id)
                    ])
                    
                    programa_ids = asignaciones.mapped('convoy_id.programa_id').ids
                    
                    # Filtrar asistencias de esos programas
                    asistencias_ids = self.with_context(disable_custom_search=True).search([
                        ('programa_id', 'in', programa_ids)
                    ]).ids
                    base_args = [('id', 'in', asistencias_ids)]
                    
                args = base_args + args

        return super(ConvoyAsistenciaServicio, self)._search(
            args,
            offset=offset,
            limit=limit,
            order=order,
            access_rights_uid=access_rights_uid
        )