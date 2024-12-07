# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime
from datetime import date
from datetime import timedelta
from babel.dates import format_date
from datetime import datetime, timedelta
from odoo.osv import expression

class ConvoyAgendarServicio(models.Model):
    _inherit = 'mz.agendar_servicio'
    
    

    convoy_id = fields.Many2one('mz.convoy', string='Convoy', required=True, tracking=True)
    convoy_id_domain = fields.Char(compute="_compute_programa_convoy_id_domain", readonly=True, store=False, )
    beneficiario_convoy_id_domain = fields.Char(compute="_compute_beneficiario_convoy_id_domain", readonly=True, store=False, )
    dependiente_convoy_id_domain = fields.Char(compute="_compute_dependiente_convoy_id_domain", readonly=True, store=False, )
    dependiente_convoy_id_domain = fields.Char(compute="_compute_dependiente_convoy_id_domain", readonly=True, store=False, )
    personal_convoy_id_domain = fields.Char(compute="_compute_personal_convoy_id_domain", readonly=True, store=False, )

    def _search(self, args, offset=0, limit=None, order=None, access_rights_uid=None):
        """
        Método _search personalizado para filtrar registros según el grupo del usuario
        """
        if self._context.get('filtrar_convoy'):  
            args = args or []
            user = self.env.user

            # Lista de grupos que no deben ver nada
            grupos_sin_acceso = [
                'manzana_convoy.group_mz_convoy_prestador_servicio',
                'manzana_convoy.group_mz_convoy_asistente_coordinador',
                'manzana_convoy.group_mz_convoy_bodeguero'
            ]

            # Si el usuario pertenece a grupos sin acceso, retornar dominio imposible
            if any(user.has_group(grupo) for grupo in grupos_sin_acceso):
                args = [('id', '=', -1)]  # Dominio imposible
            # Coordinador: ve todos los convoy donde es director_coordinador
            elif user.has_group('manzana_convoy.group_mz_convoy_coordinador'):
                convoy_ids = self.env['mz.convoy'].search([
                    ('director_coordinador.user_id', '=', user.id)
                ]).ids
                if convoy_ids:
                    args = expression.AND([args, [('convoy_id', 'in', convoy_ids)]])
                else:
                    args = [('id', '=', -1)]
            # Operador: ve solo registros de convoy en estado ejecutando donde está asignado
            elif user.has_group('manzana_convoy.group_mz_convoy_operador'):
                convoy_ids = self.env['mz.convoy'].search([
                    ('state', '=', 'ejecutando'),
                    ('operadores_ids', 'in', user.employee_id.id)
                ]).ids
                if convoy_ids:
                    args = expression.AND([args, [('convoy_id', 'in', convoy_ids)]])
                else:
                    args = [('id', '=', -1)]
            # Administrador: ve todo
            elif user.has_group('manzana_convoy.group_mz_convoy_administrador'):
                pass  # No se agregan restricciones adicionales
            # Cualquier otro grupo: no ve nada
            else:
                args = [('id', '=', -1)]

        return super(ConvoyAgendarServicio, self)._search(
            args,
            offset=offset,
            limit=limit,
            order=order,
            access_rights_uid=access_rights_uid
        )
    


    @api.model
    def get_view(self, view_id=None, view_type='form', context=None, toolbar=False, submenu=False, **kwargs):
        context = context or {}
        user = self.env.user

        # Si es operador, mostrar vistas normales
        if user.has_group('manzana_convoy.group_mz_convoy_operador'):
            if view_type == 'tree':
                view_id = self.env.ref('manzana_convoy.mz_convoy_view_agendar_servicio_tree').id
            elif view_type == 'form':
                view_id = self.env.ref('manzana_convoy.mz_convoy_view_agendar_servicio_form').id
        else:
            # Para coordinadores, administradores y otros usuarios, mostrar vistas readonly
            if view_type == 'tree':
                view_id = self.env.ref('manzana_convoy.mz_convoy_view_agendar_servicio_tree_readonly').id
            elif view_type == 'form':
                view_id = self.env.ref('manzana_convoy.mz_convoy_view_agendar_servicio_form_readonly').id

        return super().get_view(
            view_id=view_id,
            view_type=view_type,
            context=context,
            toolbar=toolbar,
            submenu=submenu,
            **kwargs
        )



    @api.onchange('fecha_solicitud')
    def _onchange_fecha_solicitud(self):
        for record in self:
            fecha_actual = datetime.now() - timedelta(hours=5)
            warning = {}

            # Caso 1: Sin convoy asignado
            if not record.convoy_id:
                if record.fecha_solicitud and record.fecha_solicitud < fecha_actual.date():
                    record.fecha_solicitud = fecha_actual.date()
                    warning = {
                        'title': "Fecha inválida",
                        'message': "La fecha ha sido ajustada a la fecha actual."
                    }
                # Limpiar el horario cuando cambia la fecha
                record.horario_id = False
            
            # Caso 2: Con convoy asignado
            else:
                if record.fecha_solicitud:
                    if not (record.convoy_id.fecha_inicio_evento <= record.fecha_solicitud <= record.convoy_id.fecha_hasta_evento):
                        raise UserError('La fecha seleccionada debe estar dentro del rango de fechas del convoy: {} - {}'.format(
                            record.convoy_id.fecha_inicio_evento.strftime('%d/%m/%Y'),
                            record.convoy_id.fecha_hasta_evento.strftime('%d/%m/%Y')
                        ))
            
            # R ornar warning si existe
            if warning:
                return {'warning': warning}
            

    @api.model
    def create(self, vals):
        if vals.get('convoy_id'):
            # Buscar la cabecera existente usando el convoy_id
            generar_horario = self.env['mz.genera.planificacion.servicio'].search([
                ('servicio_id', '=', vals.get('servicio_id')),
                ('personal_id', '=', vals.get('personal_id')),
                ('convoy_id', '=', vals.get('convoy_id')),
                ('active', '=', True),
            ], limit=1)
            
            if not generar_horario:
                raise UserError('No existe una planificación activa para este servicio y personal en el convoy seleccionado')
                
            fecha_actual = fields.Date.today()
            
            # Obtener el último número usado para esta cabecera en la misma fecha
            ultimo_horario = self.env['mz.planificacion.servicio'].search([
                ('generar_horario_id', '=', generar_horario.id),
                ('fecha', '=', fecha_actual)
            ], order='numero desc', limit=1)
            
            # Determinar el siguiente número
            siguiente_numero = (ultimo_horario.numero + 1) if ultimo_horario else 1
            
            # Crear el horario usando la cabecera existente
            horario_vals = {
                'generar_horario_id': generar_horario.id,
                'fecha': fecha_actual,
                'estado': 'activo',
                'creado_por_usuario_id': self.env.user.id,
                'turno_extra': 'no',
                'maximo_beneficiarios': generar_horario.maximo_beneficiarios,
                'numero': siguiente_numero,
                'beneficiario_ids': [(6, 0, [vals.get('beneficiario_id')])] if vals.get('beneficiario_id') else [(6, 0, [])]
            }
            
            horario = self.env['mz.planificacion.servicio'].create(horario_vals)            
            # Asignar el horario creado al registro de agendar_servicio
            vals['horario_id'] = horario.id
            vals['fecha_solicitud'] = fecha_actual
            vals['state'] = 'solicitud'            
            servicio = super(ConvoyAgendarServicio, self).create(vals)
            servicio.solicitar_horario()
            return servicio
    
    @api.onchange('personal_id')
    def _onchange_personal_id(self):
        for record in self:
            if not record.convoy_id:
                record.fecha_solicitud = False
                record.horario_id = False
                if record.servicio_id and record.personal_id:
                    domain = [
                        ('generar_horario_id.servicio_id', '=', record.servicio_id.id),
                        ('generar_horario_id.personal_id', '=', record.personal_id.id),
                        ('fecha', '>=', fields.Date.today()),
                        ('estado', '=', 'activo'),
                    ]
                    horarios_planificados = self.env['mz.planificacion.servicio'].search(domain)
                    
                    horarios_disponibles = horarios_planificados.filtered(
                        lambda h: h.beneficiarios_count < h.maximo_beneficiarios
                    )
                    if not horarios_disponibles:
                        raise UserError(f"No hay Turnos disponibles para el servicio de {record.servicio_id.servicio_id.name} con {record.personal_id.name}.")
            else:              
                fecha_actual = datetime.now() - timedelta(hours=5)
                record.fecha_solicitud = fecha_actual.date()
 
  
    @api.depends('convoy_id')
    def _compute_beneficiario_convoy_id_domain(self):
        for record in self:
            if record.convoy_id:
                beneficiario_ids = record.convoy_id.beneficiario_ids.mapped('beneficiario_id').ids
                record.beneficiario_convoy_id_domain = [('id', 'in', beneficiario_ids)]
            else:
                record.beneficiario_convoy_id_domain = [('id', 'in', [])]

    @api.depends('beneficiario_id', 'tipo_beneficiario')
    def _compute_dependiente_convoy_id_domain(self):
        for record in self:
            if record.tipo_beneficiario == 'dependiente' and record.beneficiario_id:
                # Filtrar dependientes del beneficiario seleccionado
                record.dependiente_convoy_id_domain = [('beneficiario_id', '=', record.beneficiario_id.id)]
            else:
                # Si no es dependiente o no hay beneficiario seleccionado, dominio vacío
                record.dependiente_convoy_id_domain = [('id', 'in', [])]

    @api.depends('convoy_id')
    def _compute_programa_convoy_id_domain(self):
        for record in self:
            convoy_ids =[]           
            user = self.env.user
            domain = [('state', '=', 'ejecutando')]                
            if user.has_group('manzana_convoy.group_mz_convoy_coordinador'):
                domain.append(('director_coordinador.user_id', '=', user.id))
            elif user.has_group('manzana_convoy.group_mz_convoy_operador'):
                domain.append(('operadores_ids.user_id', 'in', [user.id]))                
            convoy_ids = record.convoy_id.search(domain).ids
            record.convoy_id_domain = [('id', 'in', convoy_ids)]

    @api.depends('servicio_id')
    def _compute_personal_convoy_id_domain(self):
        for record in self:
            if record.servicio_id:
                record.personal_convoy_id_domain = [('id', 'in', record.servicio_id.personal_ids.ids)]
            else:
                record.personal_convoy_id_domain = [('id', 'in', [])]
            
    
    @api.onchange('convoy_id')
    def _onchange_field(self):
        for record in self:
            if(record.convoy_id):
                record.programa_id = record.convoy_id.programa_id
    
    