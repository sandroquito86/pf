# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class AsistenciaServicio(models.Model):
    _name = 'mz.asistencia_servicio'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Asistencia a Servicios Planificados'
    _rec_name = 'beneficiario_id'

    planificacion_id = fields.Many2one('mz.planificacion.servicio', string='Planificación', required=True, ondelete='cascade')
    beneficiario_id = fields.Many2one('mz.beneficiario', string='Beneficiario', required=True)
    fecha = fields.Date('Fecha')
    asistio = fields.Selection([('si', 'Si'), ('no', 'No'), ('pendiente', 'Pendiente')], string='Asistió', default='pendiente')
    atendido = fields.Boolean(string='Atendido', default=False)
    observacion = fields.Text(string='Observación')
    programa_id = fields.Many2one('pf.programas', string='Programa', required=True)
    servicio_id = fields.Many2one(string='Servicio', comodel_name='mz.asignacion.servicio', ondelete='restrict')
    personal_id = fields.Many2one(string='Personal', comodel_name='hr.employee', ondelete='restrict') 
    codigo = fields.Char(string='Código', readonly=True, store=True)
    tipo_servicio = fields.Selection([('normal', 'Normal'), ('medico', 'Medico')], string='Tipo de Servicio', compute='_compute_tipo_servicio')


    _sql_constraints = [
        ('unique_planificacion_beneficiario', 'unique(planificacion_id, beneficiario_id)', 
         'Ya existe un registro de asistencia para este beneficiario en esta planificación.'),
         ('unique_codigo', 'unique(codigo)', 'El código de asistencia debe ser único.')]
    
    @api.depends('servicio_id')
    def _compute_tipo_servicio(self):
        for record in self:
            record.tipo_servicio = record.servicio_id.servicio_id.tipo_servicio

    def action_asistio(self):
        self.asistio = 'si'
        self.env['mz.agendar_servicio'].search([('codigo', '=', self.codigo)]).write({'state': 'atendido'})
        

    def action_no_asistio(self):
        self.asistio = 'no'


class PlanificacionServicio(models.Model):
    _inherit = 'mz.planificacion.servicio'

    generar_horario_id = fields.Many2one(string='detalle', comodel_name='mz.genera.planificacion.servicio', ondelete='restrict')  
    beneficiarios_count = fields.Integer(string='Número de Beneficiarios', compute='_compute_beneficiarios_count',store=True)
    asistencia_ids = fields.One2many('mz.asistencia_servicio', 'planificacion_id', string='Asistencias')

    @api.constrains('asistencia_ids', 'maximo_beneficiarios')
    def _check_maximo_beneficiarios(self):
        for record in self:
            if record.beneficiarios_count > record.maximo_beneficiarios:
                raise UserError(f"No se puede exceder el número máximo de beneficiarios ({record.maximo_beneficiarios}) para este horario.")

    @api.depends('asistencia_ids')
    def _compute_beneficiarios_count(self):
        for record in self:
            record.beneficiarios_count = len(record.asistencia_ids)

    # @api.depends('fecha', 'horainicio')
    # def _compute_horario(self):
    #     for record in self:
    #         if record.fecha and record.horainicio:
    #             hora = timedelta(hours=record.horainicio)
    #             record.horario = f"{record.fecha} (hora inicio {hora.seconds // 3600:02d}:{(hora.seconds // 60) % 60:02d})"
    #         else:
    #             record.horario = False

 
   