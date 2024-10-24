# -*- coding: utf-8 -*-

from odoo import models, fields, api
from random import randint
from datetime import date
from dateutil.relativedelta import relativedelta


class SolicitudBeneficiario(models.Model):
    _name = 'gi.solicitud_beneficiario'
    _description = 'Ficha de Inscripción' 


    
    fecha = fields.Date(string='Fecha Solicitud', default=fields.Date.context_today,)
    
    STATE_SELECTION = [('borrador', 'Borrador'), ('por_aprobar', 'Por aprobar'), ('aprobado', 'Aprobado')]
    state = fields.Selection(STATE_SELECTION, 'Estado', readonly=True, default='borrador', )
    name = fields.Char(string="Nombre del Beneficiario", compute="_compute_name", store=True)
    image = fields.Image(string="Imagen del Beneficio")  # Campo para la imagen
    apellido_paterno = fields.Char(string='Apellido Paterno')
    apellido_materno = fields.Char(string='Apellido Materno')
    primer_nombre = fields.Char(string='Primer Nombre')
    segundo_nombre = fields.Char(string='Segundo Nombre')   
    fecha_nacimiento = fields.Date(string="Fecha de Nacimiento") 
    edad = fields.Char(string="Edad", compute="_compute_edad", store=True)
    cedula = fields.Char(string='Cédula de Identidad') 
    pais_id = fields.Many2one('res.country', string='Pais', ondelete='restrict')
    provincia_id = fields.Many2one("res.country.state", string='Provincia', ondelete='restrict', 
                                   domain="[('country_id', '=?', pais_id)]")   
    email = fields.Char(string='Correo Electrónico', required=True) 
    representante = fields.Char(string='Representante', required=True)
    telefono1 = fields.Char(string='Celular Principal', required=True)
    telefono2 = fields.Char(string='Celular Secundario', required=True)
    direccion = fields.Char(string='Dirección', required=True)    
    carnet_discapacidad = fields.Selection(selection=[('SI', 'SI'), ('NO', 'NO')],
                                   string='Carnet de Discapacidad',required=True)
    porcentaje_discapacidad = fields.Float(string='Descuento (%)', digits=(16, 2), default=0.0,required=True)    
    tipo_discapacidad_id = fields.Many2one(string='Tipo de discapacidad', comodel_name='pf.tipo_discapacidad', ondelete='restrict',required=True)
    
    diagnostico = fields.Text(string='Diagnóstico',required=True)
    
    servicio_ids = fields.Many2many(string='Servicios', comodel_name='gi.servicio', relation='gi_solicitud_beneficiario_servicios_rel',
                                      column1='solicitud_id', column2='servicio_id',)
    evaluacion_medica_ids = fields.Many2many(comodel_name='ir.attachment', relation='gi_solicitud_beneficiario_evaluacion_medica_rel', 
                                      column1='solicitud_id', column2='attachment_id', string='Evaluación Médica')
    cedula_beneficiario_ids = fields.Many2many(comodel_name='ir.attachment', relation='gi_solicitud_beneficiario_ci_beneficiario_rel', 
                                      column1='solicitud_id', column2='attachment_id', string='Cédula Beneficiario')
    cedula_padres_ids = fields.Many2many(comodel_name='ir.attachment', relation='gi_solicitud_beneficiario_ci_padres_rel', 
                                      column1='solicitud_id', column2='attachment_id', string='Cédula Padres')
    
    
    
    @api.depends('apellido_paterno', 'apellido_materno', 'primer_nombre', 'segundo_nombre')
    def _compute_name(self):
        for record in self:
            # Filtrar campos que no están vacíos y unirlos con un espacio
            nombres = filter(None, [
                record.apellido_paterno,
                record.apellido_materno,
                record.primer_nombre,
                record.segundo_nombre
            ])
            # Unir los nombres filtrados en una sola cadena
            record.name = " ".join(nombres) if nombres else "Nombre del Beneficiario"

    @api.depends('fecha_nacimiento')
    def _compute_edad(self):
        for record in self:
            if record.fecha_nacimiento:
                hoy = date.today()
                diferencia = relativedelta(hoy, record.fecha_nacimiento)
                record.edad = f"{diferencia.years} años, {diferencia.months} meses, {diferencia.days} días"
            else:
                record.edad = "Sin fecha de nacimiento"