# -*- coding: utf-8 -*-

from logging.config import valid_ident
import string
from odoo import models, fields, api
from odoo.exceptions import UserError
from babel.dates import format_date
# from datetime import datetime,time, datetime
import datetime
import time
import json
global NoTieneHorario

from datetime import timedelta


class GenerarHorarios(models.Model):
    _name = 'mz.genera.planificacion.servicio'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Generar Horarios'
    _rec_name = 'servicio_id'
    #_order = 'unidad_id , mes_genera'
    
    @api.model
    def _default_anio(self):
        return time.strftime('%Y')   
    name = fields.Char(string='Descripción', required=True, compute='_compute_name',)
    servicio_id = fields.Many2one(string='Servicio', comodel_name='mz.asignacion.servicio', ondelete='restrict',domain="[('programa_id', '=?', programa_id)]", required=True, tracking=True)  
    personal_id = fields.Many2one(string='Personal', comodel_name='hr.employee', ondelete='restrict',) 
    mes_genera = fields.Selection([('1', 'ENERO'), ('2', 'FEBRERO'), ('3', 'MARZO'), ('4', 'ABRIL'), ('5', 'MAYO'), ('6', 'JUNIO'), ('7', 'JULIO'), ('8', 'AGOSTO'), 
                                   ('9', 'SEPTIEMBRE'), ('10', 'OCTUBRE'), ('11', 'NOVIEMBRE'), ('12', 'DICIEMBRE')],string='Mes a Generar')
    anio = fields.Char(string='Año', default=_default_anio)
    maximo_beneficiarios = fields.Integer(string='Máximo Beneficiarios por turno', default=1, required=True)
    turno_disponibles_ids = fields.One2many(string='', comodel_name='mz.planificacion.servicio', inverse_name='generar_horario_id',)
    domain_personal_id = fields.Char(string='Domain Personal',compute='_compute_author_domain_field') 

    programa_id = fields.Many2one('pf.programas', string='Programa', required=True, tracking=True, default=lambda self: self.env.programa_id) 
    domain_programa_id = fields.Char(string='Domain Programa',compute='_compute_domain_programas')
    active = fields.Boolean(default=True, string='Activo', tracking=True)
    _sql_constraints = [('name_unique', 'UNIQUE(servicio_id,personal_id,mes_genera, anio)',
                         "Ya existe AGENDA para esta persona en el MES seleccionado !!"),]
    
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
    
    @api.depends('servicio_id', 'personal_id', 'mes_genera', 'anio')
    def _compute_name(self):
        for record in self:
            if record.servicio_id and record.personal_id and record.mes_genera and record.anio:
                mes_dict = dict(self.fields_get(allfields=['mes_genera'])['mes_genera']['selection'])
                mes_nombre = mes_dict.get(record.mes_genera, '')
                record.name = record.servicio_id.name + " - " + record.personal_id.name + " - " + mes_nombre + " - " + record.anio
            else:
                record.name = "Generar Horarios"

    

    @api.constrains('servicio_id', 'personal_id')
    def _check_detalle_generahorario(self):
        for record in self:
            if not (record.turno_disponibles_ids):
                raise UserError("No se puede guardar AGENDA sino genera detalle de Agenda!!")

    @api.constrains('servicio_id', 'personal_id')
    def _check_espe_doc_unid(self):
        for record in self:
            if not (record.servicio_id) or not (record.personal_id):
                raise UserError("Debe seleccionar UNIDAD MEDICA - ESPECIALIDAD Y MEDICO!!")

    @api.constrains('mes_genera')
    def _check_mes_genera(self):
        for record in self:
            if not (record.mes_genera):
                raise UserError("Debe elegir el MES A GENERAR!!")
            
    @api.onchange('anio')
    def _onchange_anio(self):
        for record in self:
            #capturame el año actual en una variable
            anio_actual = time.strftime('%Y')
            if anio_actual > record.anio:
                raise UserError("El año a generar no puede ser menor al año actual!!")

    @api.onchange('servicio_id')
    def _onchange_servicio_id(self):
        for record in self:
            record.personal_id = False
            record.mes_genera = False
            record.turno_disponibles_ids = False

    @api.onchange('personal_id')
    def _onchange_personal_id(self):
        for record in self:
            record.mes_genera = False
            record.turno_disponibles_ids = False
            
    def obtener_dias_del_mes(self, mes, anio):
        # Abril, junio, septiembre y noviembre tienen 30
        if mes in [4, 6, 9, 11]:
            return 30
        # Febrero depende de si es o no bisiesto
        if mes == 2:
            if self.es_bisiesto(anio):
                return 29
            else:
                return 28
        else:
            # En caso contrario, tiene 31 días
            return 31

    # Boton para generar horas
    def action_generar_horas(self):
        for record in self:
            record.turno_disponibles_ids = False
            horarios = self.env['mz.horarios.servicio'].search([('servicio_id', '=', record.servicio_id.id), ('personal_id', '=', record.personal_id.id)],limit=1)
            if not horarios:
                raise UserError("No se ha registrado horarios para este empleado en este servicio!!")
            mes = int(record.mes_genera)
            anio = int(record.anio)
            dias = record.obtener_dias_del_mes(mes, anio)
            maximo_beneficiarios = record.maximo_beneficiarios
            for horario in horarios:        
                for dia in range(dias):
                    # fecha_asignar = datetime.strptime(f'{str(anio)}-{str(mes)}-{str(dia + 1)}', '%Y-%m-%d')
                    text = str(anio)+"-"+str(mes)+"-"+str(dia+1)
                    fecha_asignar = datetime.datetime.strptime(
                        text, "%Y-%m-%d")
                    ultimo_dia_asignar = fecha_asignar.weekday()
                    #raise UserError("a {}".format(ultimo_dia_asignar))
                    horas_dia = self.env['mz.detalle.horarios'].search([('asignacion_horario_id', '=', horario.id), ('dias', '=', ultimo_dia_asignar)])                    
                    if horas_dia:
                        for horas in horas_dia:
                            
                            hora_ini = horas.horainicio
                            hi = horas.horainicio * 60
                            h1, m1 = divmod(hi, 60)
                            horafin = horas.horafin
                            hf = horas.horafin * 60
                            h2, m2 = divmod(hf, 60)
                            duracion = horas.duracionconsulta
                            # ahora si estamos
                            #raise UserError("si estamos {}".format(horas))
                            hora = '%02d:%02d-%02d:%02d' % (h1, m1, h2, m2)
                            #raise UserError("h1 {} m1 {} h2 {} m2 {}".format(h1, m1, h2, m2))
                            while round(hora_ini + duracion, 2) <= round(horafin, 2):
                                record.turno_disponibles_ids = [(0, 0, {'fecha': fecha_asignar, 'horainicio': hora_ini, 'horafin': hora_ini +
                                                                   duracion, 'hora': hora, 'maximo_beneficiarios': maximo_beneficiarios})]
                                
                                hora_ini = hora_ini + duracion 

    # generar la planificacion de las horas de las citas disponibles por especialidad, unidadmedica y medico
    @api.onchange('mes_genera', 'anio')
    def _onchange_mes_genera(self):
        for record in self:            
            if (record.mes_genera):
                if record.anio:
                    self.action_generar_horas()
                    #raise UserError("a")
                else:
                    raise UserError("Debe registrar el año a generar!!")
            else:
                record.turno_disponibles_ids = False

    @api.onchange('personal_id')
    def _onchange_doctor(self):
        for record in self:
            record.mes_genera = False

    @api.onchange('anio')
    def _onchange_anio(self):
        for record in self:
            record.mes_genera = False   

    def es_bisiesto(self, anio):
        return anio % 4 == 0 and (anio % 100 != 0 or anio % 400 == 0) 


    

class PlanificacionServicio(models.Model):
    _name = 'mz.planificacion.servicio'
    _description = 'Planificacion de Turnos'
    _rec_name = 'horario'
    _order = 'fecha, horainicio ASC'

    horario = fields.Char(string='Horario',
                          compute='_compute_horario')
     
    generar_horario_id = fields.Many2one(string='detalle', comodel_name='mz.genera.planificacion.servicio', ondelete='restrict',)
    fecha = fields.Date()
    horainicio = fields.Float(string='Hora de Inicio', index=True,)
    horafin = fields.Float(string='Hora Fin', index=True,)
    hora = fields.Char(string='Hora')    
    beneficiario_ids = fields.Many2many(string='Beneficiarios', comodel_name='mz.beneficiario', relation='mz_planificacion_servicio_beneficiario_rel',)
    estado = fields.Boolean(default='True')    
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