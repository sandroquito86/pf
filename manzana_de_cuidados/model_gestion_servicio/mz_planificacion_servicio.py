# -*- coding: utf-8 -*-

from logging.config import valid_ident
import string
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from babel.dates import format_date
# from datetime import datetime,time, datetime
from datetime import datetime
from datetime import date
import time
import json
global NoTieneHorario

from datetime import timedelta


class GenerarHorarios(models.Model):
    _name = 'mz.genera.planificacion.servicio'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Generar Horarios'
    _rec_name = 'servicio_id'
    
      
    name = fields.Char(string='Descripción', required=True, compute='_compute_name',)
    servicio_id = fields.Many2one(string='Servicio', comodel_name='mz.asignacion.servicio', ondelete='restrict',domain="[('programa_id', '=?', programa_id)]", required=True, tracking=True)  
    personal_id = fields.Many2one(string='Personal', comodel_name='hr.employee', ondelete='restrict',) 
    
    # hay que eliminar estos campos ya que fuerin reemplados por fecha inicio y fecha de fin
    # mes_genera = fields.Selection([('1', 'ENERO'), ('2', 'FEBRERO'), ('3', 'MARZO'), ('4', 'ABRIL'), ('5', 'MAYO'), ('6', 'JUNIO'), ('7', 'JULIO'), ('8', 'AGOSTO'), 
    #                                ('9', 'SEPTIEMBRE'), ('10', 'OCTUBRE'), ('11', 'NOVIEMBRE'), ('12', 'DICIEMBRE')],string='Mes a Generar')
    # anio = fields.Char(string='Año', default=_default_anio)
    maximo_beneficiarios = fields.Integer(string='Máximo Beneficiarios por turno', default=1, required=True)
    turno_disponibles_ids = fields.One2many(string='', comodel_name='mz.planificacion.servicio', inverse_name='generar_horario_id',)
    domain_personal_id = fields.Char(string='Domain Personal',compute='_compute_author_domain_field') 

    programa_id = fields.Many2one('pf.programas', string='Programa', required=True, tracking=True, default=lambda self: self.env.programa_id) 
    domain_programa_id = fields.Char(string='Domain Programa',compute='_compute_domain_programas')
    active = fields.Boolean(default=True, string='Activo', tracking=True)
    # _sql_constraints = [('name_unique', 'UNIQUE(servicio_id,personal_id)',
    #                      "Ya existe AGENDA para esta persona en el MES seleccionado !!"),]
    
    fecha_inicio = fields.Date(string='Fecha Inicio')
    fecha_fin = fields.Date(string='Fecha Fin')

    es_replanificacion = fields.Boolean('Es Replanificación', default=False)
    planificacion_original_id = fields.Many2one('mz.genera.planificacion.servicio', 'Planificación Original')
    estado = fields.Selection([
        ('borrador', 'Borrador'),
        ('confirmado', 'Confirmado'),
        ('replanificado', 'Replanificado'),
        ('cancelado', 'Cancelado')
    ], string='Estado', default='borrador')

    
    # Constrain que valida que no existan planificacion que se crucen entre fechas de la misma persona y servicio 
    @api.constrains('servicio_id', 'personal_id', 'fecha_inicio', 'fecha_fin')
    def _check_overlapping_schedules(self):
        for record in self:
            # Buscar planificaciones existentes para la misma persona y servicio
            overlapping_schedules = self.search([
                ('id', '!=', record.id),  # Excluir el registro actual
                ('servicio_id', '=', record.servicio_id.id),
                ('personal_id', '=', record.personal_id.id),
                # Condiciones para detectar superposición
                ('fecha_inicio', '<=', record.fecha_fin),
                ('fecha_fin', '>=', record.fecha_inicio),
                ('estado', '=', 'confirmado')
            ])
            
            if overlapping_schedules:
                raise UserError(
                    f"No se puede crear la planificación. Ya existe una planificación para el servicio {record.servicio_id.name} "
                    f"con el personal {record.personal_id.name} que se superpone en el rango de fechas."
                )

    @api.depends('servicio_id')
    def _compute_domain_programas(self):
        for record in self:
            programas = self.env['pf.programas'].search([('modulo_id', '=', self.env.ref('prefectura_base.modulo_2').id)])
            if programas:
                record.domain_programa_id = [('id', 'in', programas.ids)]
            else:
                record.domain_programa_id = [('id', 'in', [])]

    @api.depends('servicio_id')
    def _compute_author_domain_field(self):
        for record in self:
            if record.servicio_id:
                empleados = self.env['mz.asignacion.servicio'].search([('id', '=', record.servicio_id.id)]).mapped('personal_ids')
                if empleados:
                    record.domain_personal_id = [('id', 'in', empleados.ids)]
                else:
                    record.domain_personal_id = [('id', 'in', [])]
            else:
                record.domain_personal_id = [('id', 'in', [])]
    
    @api.depends('servicio_id', 'personal_id', 'fecha_inicio', 'fecha_fin')
    def _compute_name(self):
        for record in self:
            if record.servicio_id and record.personal_id and record.fecha_inicio and record.fecha_fin:
                # mes_dict = dict(self.fields_get(allfields=['mes_genera'])['mes_genera']['selection'])
                # mes_nombre = mes_dict.get(record.mes_genera, '')
                record.name = record.servicio_id.name + " - " + record.personal_id.name + " - " + str(record.fecha_inicio) + " a " + str(record.fecha_fin)
            else:
                record.name = "Generar Horarios"

    

    @api.constrains('servicio_id', 'personal_id')
    def _check_detalle_generahorario(self):
        for record in self:
            if not (record.turno_disponibles_ids) and not record.es_replanificacion:
                raise UserError("No se puede guardar AGENDA sino genera detalle de Agenda!!")

    @api.constrains('servicio_id', 'personal_id')
    def _check_espe_doc_unid(self):
        for record in self:
            if not (record.servicio_id) or not (record.personal_id):
                raise UserError("Debe seleccionar UNIDAD MEDICA - ESPECIALIDAD Y MEDICO!!")

    @api.constrains('fecha_inicio','fecha_fin')
    def _check_fecha(self):
        for record in self:
            if not record.fecha_inicio or not record.fecha_fin:
                if not record.es_replanificacion:
                    raise UserError("Debe elegir las FECHAS A GENERAR!!")
            
    @api.onchange('fecha_inicio')
    def _onchange_fecha_inicio(self):
        for record in self:
            if record.fecha_inicio:
                fecha_actual = fields.Date.today()
                if fecha_actual > record.fecha_inicio:
                    raise UserError("La fecha de inicio no puede ser menor al la fecha actual!!")

    @api.onchange('servicio_id')
    def _onchange_servicio_id(self):
        for record in self:
            record.personal_id = False
            record.fecha_inicio = False
            record.fecha_fin = False
            record.turno_disponibles_ids = False

    @api.onchange('personal_id')
    def _onchange_personal_id(self):
        for record in self:
            record.fecha_inicio = False
            record.fecha_fin = False
            record.turno_disponibles_ids = False
            
    # def obtener_dias_del_mes(self, mes, anio):
    #     # Abril, junio, septiembre y noviembre tienen 30
    #     if mes in [4, 6, 9, 11]:
    #         return 30
    #     # Febrero depende de si es o no bisiesto
    #     if mes == 2:
    #         if self.es_bisiesto(anio):
    #             return 29
    #         else:
    #             return 28
    #     else:
    #         # En caso contrario, tiene 31 días
            # return 31

    # Boton para generar horas
    def action_generar_horas(self):
        for record in self:
            record.turno_disponibles_ids = False
            horarios = self.env['mz.horarios.servicio'].search([
                ('servicio_id', '=', record.servicio_id.id), 
                ('personal_id', '=', record.personal_id.id)
            ], limit=1)
            
            if not horarios:
                raise UserError("No se ha registrado horarios para este empleado en este servicio!!")

            # Asumiendo que agregamos campos para fecha_inicio y fecha_fin de la semana
            fecha_inicio = record.fecha_inicio
            fecha_fin = record.fecha_fin
                
            maximo_beneficiarios = record.maximo_beneficiarios
            
            for horario in horarios:
                fecha_actual = fecha_inicio
                while fecha_actual <= fecha_fin:
                    ultimo_dia_asignar = fecha_actual.weekday()
                    
                    horas_dia = self.env['mz.detalle.horarios'].search([
                        ('asignacion_horario_id', '=', horario.id), 
                        ('dias', '=', ultimo_dia_asignar)
                    ])
                    
                    if horas_dia:
                        for horas in horas_dia:
                            hora_ini = horas.horainicio
                            hi = horas.horainicio * 60
                            h1, m1 = divmod(hi, 60)
                            horafin = horas.horafin
                            hf = horas.horafin * 60
                            h2, m2 = divmod(hf, 60)
                            duracion = horas.duracionconsulta
                            
                            hora = '%02d:%02d-%02d:%02d' % (h1, m1, h2, m2)
                            
                            while round(hora_ini + duracion, 2) <= round(horafin, 2):
                                record.turno_disponibles_ids = [(0, 0, {
                                    'fecha': fecha_actual,
                                    'horainicio': hora_ini,
                                    'horafin': hora_ini + duracion,
                                    'hora': hora,
                                    'maximo_beneficiarios': maximo_beneficiarios
                                })]
                                hora_ini = hora_ini + duracion
                    
                    fecha_actual += timedelta(days=1)
                    
        return True


    # generar la planificacion de las horas de las citas disponibles por especialidad, unidadmedica y medico
    @api.onchange('fecha_inicio', 'fecha_fin')
    def _onchange_genera_planificacion(self):
        for record in self:            
            if record.fecha_inicio and record.fecha_fin:
                if record.fecha_inicio > record.fecha_fin:
                    raise UserError("La fecha de inicio no puede ser mayor a la fecha de fin")
                self.action_generar_horas()
            else:
                record.turno_disponibles_ids = False

    def action_replanificar(self):
        """Crear una nueva planificación basada en la actual"""
        self.ensure_one()
        if self.estado != 'confirmado':
            raise UserError('Solo se pueden replanificar turnos confirmados')
            
        # Crear nueva planificación
        nueva_planificacion = self.copy({
            'es_replanificacion': True,
            'planificacion_original_id': self.id,
            'estado': 'borrador',
            'fecha_inicio': False,  # Se establecerá en el wizard
            'fecha_fin': False,     # Se establecerá en el wizard
            'turno_disponibles_ids': False  # Los turnos se generarán después
        })
        
        # Crear y retornar la acción del wizard con todos los parámetros necesarios
        action = {
            'name': _('Replanificar Turnos'),
            'type': 'ir.actions.act_window',
            'res_model': 'mz.wizard.replanificar.turnos',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'views': [(False, 'form')],
            'context': {
                'default_planificacion_id': nueva_planificacion.id,
                'default_planificacion_original_id': self.id,
                'default_fecha_inicio': fields.Date.today(),
                'form_view_ref': False,
                'active_model': self._name,
                'active_id': self.id,
                'active_ids': [self.id],
            },
            'flags': {
                'action_buttons': True,
                'headless': True,
            }
        }
        return action
    
    def action_confirmar(self):
        self.ensure_one()
        if self.es_replanificacion and self.planificacion_original_id:
            self.planificacion_original_id.estado = 'replanificado'
        self.estado = 'confirmado'
        
    def action_cancelar(self):
        self.ensure_one()
        self.estado = 'cancelado'

    # def es_bisiesto(self, anio):
    #     return anio % 4 == 0 and (anio % 100 != 0 or anio % 400 == 0) 


    

class PlanificacionServicio(models.Model):
    _name = 'mz.planificacion.servicio'
    _description = 'Planificacion de Turnos'
    _rec_name = 'horario'
    _order = 'fecha, horainicio ASC'

    horario = fields.Char(string='Horario',
                          compute='_compute_horario')
     
    generar_horario_id = fields.Many2one(string='Cabecera', comodel_name='mz.genera.planificacion.servicio', ondelete='restrict',)
    fecha = fields.Date()
    horainicio = fields.Float(string='Hora de Inicio', index=True,)
    horafin = fields.Float(string='Hora Fin', index=True,)
    hora = fields.Char(string='Hora')    
    beneficiario_ids = fields.Many2many(string='Beneficiarios', comodel_name='mz.beneficiario', relation='mz_planificacion_servicio_beneficiario_rel',)
    estado = fields.Selection([('activo', 'Activo'), ('inactivo', 'Inactivo')], string='Estado', default='activo')
    observacion = fields.Char(string='Observación')
    fecha_actualizacion = fields.Date(string='Fecha Actualiza', readonly=True, default=fields.Datetime.now, )
    maximo_beneficiarios = fields.Integer(string='Beneficiarios Maximos', default=1, required=True)
    dia = fields.Char(string='Dia', compute='_compute_dia', store=True)

    @api.depends('fecha')
    def _compute_dia(self):
        for record in self:
            if record.fecha:
                record.dia = format_date(record.fecha, 'EEEE', locale='es_ES')
            else:
                record.dia = ''

    @api.depends('fecha', 'horainicio', 'horafin', 'dia')
    def _compute_horario(self):
        for record in self:
            if record.fecha and record.horainicio and record.horafin:
                hora_inicio = str(timedelta(hours=record.horainicio)).rsplit(':', 1)[0]
                hora_fin = str(timedelta(hours=record.horafin)).rsplit(':', 1)[0]
                record.horario = f"{record.dia} (hora inicio: {hora_inicio}, hora fin: {hora_fin})"
            else:
                record.horario = ''


class WizardReplanificarTurnos(models.TransientModel):
    _name = 'mz.wizard.replanificar.turnos'
    _description = 'Wizard para Replanificar Turnos'

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'fecha_inicio' in fields_list and not res.get('fecha_inicio'):
            res['fecha_inicio'] = fields.Date.today()
        if 'fecha_fin' in fields_list and not res.get('fecha_fin'):
            res['fecha_fin'] = fields.Date.today() + timedelta(days=6)
        return res

    planificacion_id = fields.Many2one(
        'mz.genera.planificacion.servicio', 
        'Nueva Planificación',
        required=True
    )
    planificacion_original_id = fields.Many2one(
        'mz.genera.planificacion.servicio', 
        'Planificación Original',
        required=True
    )
    fecha_inicio = fields.Date(
        'Nueva Fecha Inicio', 
        required=True
    )
    fecha_fin = fields.Date(
        'Nueva Fecha Fin', 
        required=True
    )
    motivo_replanificacion = fields.Text(
        'Motivo de Replanificación', 
        required=True
    )

    # @api.onchange('fecha_inicio')
    # def _onchange_fecha_inicio(self):
    #     if self.fecha_inicio:
    #         self.fecha_fin = self.fecha_inicio + timedelta(days=6)
    
    def action_replanificar(self):
        self.ensure_one()       
        if self.fecha_inicio < fields.Date.today():
            raise UserError('No se puede replanificar para fechas pasadas')
        
        self.planificacion_original_id.write({
            'estado': 'replanificado'
        })
        turnos_a_inactivar = self.env['mz.planificacion.servicio'].search([
            ('generar_horario_id', '=', self.planificacion_original_id.id), ('fecha', '>=', self.fecha_inicio), ('fecha', '<=', self.fecha_fin)
        ])
        if turnos_a_inactivar:
            turnos_a_inactivar.write({
                'estado': 'inactivo'
            })
            reagendar_servicio = self.env['mz.agendar_servicio'].search([('horario_id', 'in', turnos_a_inactivar.ids)])
            if reagendar_servicio:
                reagendar_servicio.write({
                'state': 'por_reeplanificar'
                })
            archivar_asistencia = self.env['mz.asistencia_servicio'].search([('planificacion_id', 'in', turnos_a_inactivar.ids)])
            if archivar_asistencia:
                archivar_asistencia.write({
                'active': False
                })

            
        # Actualizar la nueva planificación
        self.planificacion_id.write({
            'fecha_inicio': self.fecha_inicio,
            'fecha_fin': self.fecha_fin
        })
        
        # Generar nuevos turnos
        self.planificacion_id.action_generar_horas()
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mz.genera.planificacion.servicio',
            'res_id': self.planificacion_id.id,
            'view_mode': 'form',
            'target': 'current',
        }