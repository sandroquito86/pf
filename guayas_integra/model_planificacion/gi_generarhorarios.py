# -*- coding: utf-8 -*-

from logging.config import valid_ident
import string
from odoo import models, fields, api
from odoo.exceptions import ValidationError
# from datetime import datetime,time, datetime
import datetime
import time
import json
global NoTieneHorario


class GenerarHorarios(models.Model):
    _name = 'gi.generarhorarios'
    _description = 'Generar Horarios'
    _rec_name = 'servicio_id'
    #_order = 'unidad_id , mes_genera'

    @api.model
    def _default_anio(self):
        return time.strftime('%Y')   

    servicio_id = fields.Many2one(comodel_name='gi.servicio', string='Servicio', required=True)    
    personal_id = fields.Many2one(comodel_name='gi.personal', tracking=True, required=True)
    mes_genera = fields.Selection([('1', 'ENERO'), ('2', 'FEBRERO'), ('3', 'MARZO'), ('4', 'ABRIL'), ('5', 'MAYO'), ('6', 'JUNIO'), ('7', 'JULIO'), ('8', 'AGOSTO'), 
                                   ('9', 'SEPTIEMBRE'), ('10', 'OCTUBRE'), ('11', 'NOVIEMBRE'), ('12', 'DICIEMBRE')],string='Mes a Generar')
    anio = fields.Char(string='Año', default=_default_anio)
    turno_disponibles_ids = fields.One2many(string='', comodel_name='gi.generar_turnos', inverse_name='generar_horario_id',)
    

    _sql_constraints = [('name_unique', 'UNIQUE(servicio_id,personal_id,mes_genera, anio)',
                         "Ya existe AGENDA para esta persona en el MES seleccionado !!"),]

    @api.constrains('servicio_id', 'personal_id')
    def _check_detalle_generahorario(self):
        for record in self:
            if not (record.turno_disponibles_ids):
                raise ValidationError("No se puede guardar AGENDA sino genera detalle de Agenda!!")

    @api.constrains('servicio_id', 'personal_id')
    def _check_espe_doc_unid(self):
        for record in self:
            if not (record.servicio_id) or not (record.personal_id):
                raise ValidationError("Debe seleccionar UNIDAD MEDICA - ESPECIALIDAD Y MEDICO!!")

    @api.constrains('mes_genera')
    def _check_mes_genera(self):
        for record in self:
            if not (record.mes_genera):
                raise ValidationError("Debe elegir el MES A GENERAR!!")
            
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
            self.turno_disponibles_ids = False
            horarios = self.env['gi.asignacion_horario'].search([('servicio_id', '=', self.servicio_id.id), ('personal_id', '=', self.personal_id.id)])
            mes = int(self.mes_genera)
            anio = int(self.anio)
            dias = self.obtener_dias_del_mes(mes, anio)
            for horario in horarios:        
                for dia in range(dias):
                    # fecha_asignar = datetime.strptime(f'{str(anio)}-{str(mes)}-{str(dia + 1)}', '%Y-%m-%d')
                    text = str(anio)+"-"+str(mes)+"-"+str(dia+1)
                    fecha_asignar = datetime.datetime.strptime(
                        text, "%Y-%m-%d")
                    ultimo_dia_asignar = fecha_asignar.weekday()
                    #raise ValidationError("a {}".format(ultimo_dia_asignar))
                    horas_dia = self.env['gi.detalle_horarios'].search([('asignacion_horario_id', '=', horario.id), ('dias', '=', ultimo_dia_asignar)])                    
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
                            #raise ValidationError("si estamos {}".format(horas))
                            hora = '%02d:%02d-%02d:%02d' % (h1, m1, h2, m2)
                            #raise ValidationError("h1 {} m1 {} h2 {} m2 {}".format(h1, m1, h2, m2))
                            while round(hora_ini + duracion, 2) <= round(horafin, 2):
                                self.turno_disponibles_ids = [(0, 0, {'fecha': fecha_asignar, 'horainicio': hora_ini, 'horafin': hora_ini +
                                                                   duracion, 'hora': hora})]
                                
                                hora_ini = hora_ini + duracion 

    # generar la planificacion de las horas de las citas disponibles por especialidad, unidadmedica y medico
    @api.onchange('mes_genera', 'anio')
    def _onchange_mes_genera(self):
        for record in self:            
            if (record.mes_genera):
                if record.anio:
                    self.action_generar_horas()
                    #raise ValidationError("a")
                else:
                    raise ValidationError("Debe registrar el año a generar!!")
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


    

class TurnosDisponibles(models.Model):
    _name = 'gi.generar_turnos'
    _description = 'Generación de Turnos'
    _rec_name = 'horario'
    _order = 'fecha, horainicio ASC'

    horario = fields.Char(string='Horario',
                          compute='_compute_horario')

    @api.depends('fecha', 'horainicio')
    def _compute_horario(self):
        for record in self:
            if (record.fecha and record.horainicio):
                record.horario = str(record.fecha) + " (hora inicio " + str(
                    datetime.timedelta(hours=record.horainicio)).rsplit(':', 1)[0] + ")"
    generar_horario_id = fields.Many2one(string='detalle', comodel_name='gi.generarhorarios', ondelete='restrict',)
    fecha = fields.Date()
    horainicio = fields.Float(string='Hora de Inicio', index=True,)
    horafin = fields.Float(string='Hora Fin', index=True,)
    hora = fields.Char(string='Hora')    
   # beneficiario_id = fields.Many2one(string='Paciente', comodel_name='gi.beneficiario', ondelete='restrict')
    estado = fields.Boolean(default='True')    
    observacion = fields.Char(string='Observación')
    fecha_actualizacion = fields.Date(string='Fecha Actualiza', readonly=True, default=fields.Datetime.now, )
  