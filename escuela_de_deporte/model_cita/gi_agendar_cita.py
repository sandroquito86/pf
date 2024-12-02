# -*- coding: utf-8 -*-
import json
import logging
import time
from datetime import date, datetime, timedelta

import requests
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import format_date



_logger = logging.getLogger(__name__)


class AgendamientoServicio(models.Model):
    _name = 'gi.agendar_cita'
    _description = 'Agendamiento de Servicio'
    _inherit =  ['mail.thread', 'mail.activity.mixin'] # 'gi.especialidad'
    _rec_name = 'doctor_id'
    _order = 'fecha_solicitud DESC'

    

    @api.depends('paciente_id')
    def _compute_crear_cita(self):
        for record in self:
            paciente_id = self.env['gi.paciente'].search(
                [('current_user', '=', self.env.user.id)], limit=1)
            if (paciente_id):
                if (paciente_id.tipo_paciente == 'neonato') or (paciente_id.tipo_paciente == False):
                    record.band_crear = True
                else:
                    record.band_crear = False
            else:
                record.band_crear = False
        
   

       
    
    band_crear = fields.Boolean(string='Crear', compute="_compute_crear_cita")
    paciente_id = fields.Many2one(string='Paciente', comodel_name='gi.paciente',
                                  ondelete='restrict', tracking=True, required=True)
    unidad_id = fields.Many2one(
        'gi.unidadmedica', string='Unidad Medica', tracking=True, required=True)
    doctor_id = fields.Many2one(
        comodel_name='gi.doctor', tracking=True, required=True)
    
    fecha_creacion_cita = fields.Date(
        string='Fecha Creación', readonly=True, default=fields.Datetime.now, )

    
    horario_id = fields.Many2one(string='Horarios', comodel_name='gi.detalle.generahorarios',
                                 ondelete='restrict', tracking=True, required=True)

    tipocons = fields.Selection(
        related='horario_id.tipocons', readonly=True, store=True)

    edad = fields.Char(string='Duracion', compute=_compute_edad)

    STATE_SELECTION = [('borrador', 'Borrador'), ('agendado', 'Agendado'),
                       ('atendido', 'Atendido'), ('anulado', 'Anulado')]

    state = fields.Selection(STATE_SELECTION, 'Estado', readonly=True,
                             track_visibility='onchange', default='borrador', )
    fecha_solicitud = fields.Date(
        string='Fecha Cita', compute="_compute_fecha_solicitud", readonly=True, store=True)
    fecha_anulacion = fields.Datetime(string='Fecha Anulación')
    active = fields.Boolean(default='True')
    observacion = fields.Char(string='Observación')
    anulacion = fields.Text(string='Motivo Anulación')
    # con esto hasta podrian sacar el porcentaje de registros q vienen de cada fuente
    origen_registro = fields.Selection([
        ('odoo', 'Odoo'),  # Esto indicaria que fue por uso del sistema odoo
        ('mssql', 'MSSQL'),  # Esto indicaria q viene del trigger
        ('mobile', 'App')
    ], default='odoo')  # con default odoo no tienes q cambiar mayor cosa q ya tienes
    # solo revisar el create que solo invoque al REST si es odoo, ni siquiera debe estar en la UI, es solo de control interno

    warning = {
        'title': 'Mensaje de error',
        'message': ''
    }

    @api.constrains('unidad_id', 'especialidad_id', 'state', 'active')
    def _check_no_duplicado(self):
        for record in self:
            # raise ValidationError("llwe")
            cita = self.search(
                [('id', '!=', self.id), ('paciente_id', '=', record.paciente_id.id), ('especialidad_id', '=',
                                                                                      self.especialidad_id.id),
                 ('state', '=', 'agendado'), ('active', '=', True), ('horario_id.turnofact', '=', False),('horario_id.fecha', '>', datetime.now().date())])
            # cita = self.search([('id', '!=',self.id),('especialidad_id', '=',self.especialidad_id.id),('state', '=',self.state)])
            # raise ValidationError(self.id)
            if cita:
                raise ValidationError(
                    "Ya tiene una cita médica agendada en la especialidad seleccionada !!")

    @api.constrains('horario_id')
    def _check_mes_genera(self):
        for record in self:
            if not (record.horario_id):
                raise ValidationError("Debe elegir HORARIO!!")

    @api.constrains('paciente_id')
    def _check_mes_genera(self):
        for record in self:
            if not (record.paciente_id):
                raise ValidationError("Debe elegir PACIENTE Agendar!!")

    def action_anulacion(self):
        # raise ValidationError(str(datetime.timestamp(
        #     datetime.now().time().strftime("%H:%M"))).rsplit(':', 1)[0])

        # conversion_hora = datetime.now().time().hour + datetime.now().time().minute/60.0
        # raise ValidationError(
        #     datetime.now().time().hour + datetime.now().time().minute/60.0)
        # if self.fecha_solicitud <= datetime.now().date():
        hoy = datetime.now().date()

        if self.fecha_solicitud <= hoy:
            raise ValidationError(
                "No se puede anular citas médicas MENORES O IGUAL a la FECHA DE HOY")
        
        for record in self:
            record.horario_id.paciente_id = False
            self.write({'state': 'anulado', 'active': False,
                        'fecha_anulacion': time.strftime('%Y-%m-%d %H:%M:%S')})

            # if self.state == 'anulado' and self.observacion == False:
            #     #   if self.state == 'agendado' and self.observacion == '':
            #     raise ValidationError(
            #         "Debe ingresar Motivo de Anulación!!")

            # inicio invocación al REST API para anular cita medica en SQL
            request = {'cmd': 'TrspTurnos_Eliminados_WebOdoo', 'params': {
                'doctor': self.doctor_id.codigo,
                'especialidad': self.especialidad_id.codigo,
                'unidad_medica': self.unidad_id.codigo,
                'fecha_cita': datetime.strftime(self.horario_id.fecha, '%Y-%m-%d'),
                'hora_cita': '%s-%s' % (
                    str(timedelta(hours=self.horario_id.hora_inicio)).rsplit(
                        ':', 1)[0],
                    str(timedelta(hours=self.horario_id.hora_fin)).rsplit(
                        ':', 1)[0]
                ),
                # entonces debes convertir ese float al formato q necesita mssql
                'issfa_pcte': self.paciente_id.issfa,
                'cedula_pcte': self.paciente_id.cedula,
                'hcu_pcte': self.paciente_id.hcu,
                'nombre_pcte': self.paciente_id.nombre,
                'tipo_consulta': self.horario_id.tipocons,
                'usuario_elimina': str(self.env.user.login),
                'fecha_reserva_cita': datetime.strftime(self.create_date, '%Y-%m-%d %H:%M:%S'),
                'observacion': self.anulacion,
                # etc
            }}
            _logger.info(request)
            # raise ValidationError(request)
            # se copia lo que ponga en la consola esta línea
            # y se prueba desde postman hasta encontrar la solución
            endpoint = self.env['ir.config_parameter'].sudo(
            ).get_param('rest_api_endpoint')
            _logger.info(endpoint)
            response = requests.post('%s/api/v1/call-proc' %
                                     endpoint, json.dumps(request), timeout=60)
            response.raise_for_status()
            response = json.loads(response.content)
            _logger.info(response)
            # FIN invocación al REST API

    
    
    especialidad_id = fields.Many2one(
        comodel_name='gi.especialidad', tracking=True, required=True)

    # depende de especialidad gi
    

    @api.depends('horario_id')
    def _compute_fecha_solicitud(self):
        for record in self:
            record.fecha_solicitud = record.horario_id.fecha

    # depende de especialidad y reparto gi

    
    @api.onchange('fecha_creacion_cita')
    def _onchange_paciente_id(self):
        for record in self:
            if self.user_has_groups('turnos.group_turnos_especificos_paciente'):
                paciente_id = self.env['gi.paciente'].search(
                    [('current_user', '=', self.env.user.id)], limit=1)
                record.paciente_id = paciente_id.id

    @api.onchange('paciente_id')
    def _onchange_paciente(self):
        for record in self:
            record.doctor_id = False
            record.especialidad_id = False
            record.horario_id = False
            record.unidad_id = False

    @api.onchange('unidad_id')
    def _onchange_unidadmedica(self):
        for record in self:
            record.doctor_id = False
            record.especialidad_id = False
            record.horario_id = False
            if (record.unidad_id ):
                parametro_id = self.env['gi.parametro'].search(
                            [('id', '=', 1)], limit=1)
                
                espec_activa = self.env["gi.especialidad"].search(
                                [ ('web', '=', True)])
                
                if not espec_activa:
                    raise ValidationError(f"No Existen Especialidades Disponibles  . {parametro_id.mensaje} . ")


    @api.onchange('doctor_id')
    def _onchange_doctor(self):
        for record in self:
            record.horario_id = False

  
    @api.model
    def create(self, values):
        result = super(AgendamientoServicio, self).create(values)
        result.horario_id.write({'paciente_id': result.paciente_id.id})
        result.state = "agendado"
        return result
 
    def unlink(self):
        self.action_anulacion()
        result = super(AgendamientoServicio, self).unlink()
        return result
