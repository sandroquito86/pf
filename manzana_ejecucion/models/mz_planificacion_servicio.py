# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class AsistenciaServicio(models.Model):
    _name = 'mz.asistencia_servicio'
    _description = 'Asistencia a Servicios Planificados'

    planificacion_id = fields.Many2one('mz.planificacion.servicio', string='Planificación', required=True, ondelete='cascade')
    beneficiario_id = fields.Many2one('mz.beneficiario', string='Beneficiario', required=True)
    fecha = fields.Date('Fecha')
    asistio = fields.Boolean(string='Asistió', default=False)
    observacion = fields.Text(string='Observación')

    _sql_constraints = [
        ('unique_planificacion_beneficiario', 'unique(planificacion_id, beneficiario_id)', 
         'Ya existe un registro de asistencia para este beneficiario en esta planificación.')]

class PlanificacionServicio(models.Model):
    _inherit = 'mz.planificacion.servicio'

    generar_horario_id = fields.Many2one(string='detalle', comodel_name='mz.genera.planificacion.servicio', ondelete='restrict')
    horario = fields.Char(string='Horario', compute='_compute_horario')   
    beneficiarios_count = fields.Integer(string='Número de Beneficiarios', compute='_compute_beneficiarios_count',store=True)
    asistencia_ids = fields.One2many('mz.asistencia_servicio', 'planificacion_id', string='Asistencias')

    @api.constrains('asistencia_ids', 'maximo_beneficiarios')
    def _check_maximo_beneficiarios(self):
        for record in self:
            if record.beneficiarios_count > record.maximo_beneficiarios:
                raise ValidationError(f"No se puede exceder el número máximo de beneficiarios ({record.maximo_beneficiarios}) para este horario.")

    @api.depends('asistencia_ids')
    def _compute_beneficiarios_count(self):
        for record in self:
            record.beneficiarios_count = len(record.asistencia_ids)

    @api.depends('fecha', 'horainicio')
    def _compute_horario(self):
        for record in self:
            if record.fecha and record.horainicio:
                hora = timedelta(hours=record.horainicio)
                record.horario = f"{record.fecha} (hora inicio {hora.seconds // 3600:02d}:{(hora.seconds // 60) % 60:02d})"
            else:
                record.horario = False
                

 
   