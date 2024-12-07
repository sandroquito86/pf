# -*- coding: utf-8 -*-

from odoo.exceptions import UserError
from odoo import models, fields, api
import re
from random import randint
from datetime import date
from dateutil.relativedelta import relativedelta
from .. import utils

class Dependiente(models.Model):
    _name = 'mz.dependiente'
    _description = 'Dependiente'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    
    @api.model
    def _get_tipo_dependiente_domain(self):
        catalogo_id = self.env.ref('prefectura_base.tipo_dependiente').id
        return [('catalogo_id', '=', catalogo_id)]
    

    name = fields.Char(string='Nombre Completo', required=True, compute='_compute_name', tracking=True)
    tipo_dependiente = fields.Many2one('pf.items', string="Tipo de Dependiente", required=True, ondelete="cascade", domain=_get_tipo_dependiente_domain , tracking=True)
    primer_apellido = fields.Char(string='Primer Apellido', required=True, tracking=True)
    segundo_apellido = fields.Char(string='Segundo Apellido', tracking=True)
    primer_nombre = fields.Char(string='Primer Nombre', required=True, tracking=True)
    segundo_nombre = fields.Char(string='Segundo Nombre', tracking=True)
    fecha_nacimiento = fields.Date(string='Fecha de Nacimiento', tracking=True)
    historia_clinica_ids = fields.One2many('mz.historia.clinica', 'dependiente_id', string='Historias Clínicas')
    consulta_count = fields.Integer(string='Número de Consultas', compute='_compute_consulta_count')
    historia_psicologica_ids = fields.One2many('mz.historia.psicologica', 'dependiente_id', string='Historias Psicológicas')
    consulta_psicolociga_count = fields.Integer(string='Número de Consultas Psicológicas', compute='_compute_consulta_psicologica_count')
    tipo_documento = fields.Selection([
        ('dni', 'DNI'),
        ('pasaporte', 'Pasaporte'),
        ('carnet_extranjeria', 'Carnet de Extranjería')
    ], string='Tipo de Documento', required=True, tracking=True)
    numero_documento = fields.Char(string='Número de Documento', required=True, tracking=True)
    beneficiario_id = fields.Many2one('mz.beneficiario', string='Beneficiario', ondelete='cascade', required=True)
    edad = fields.Char(string="Edad", compute="_compute_edad", store=True)
    genero_id = fields.Many2one('pf.items', string='Género', domain="[('catalogo_id', '=', ref('prefectura_base.genero'))]")
    # creame un constrains para que el numero_documento y tipo_documento sean unico 

    _sql_constraints = [('unique_documento', 'UNIQUE(tipo_documento, numero_documento)', 'Ya existe un dependiente con este documento.')]

    @api.depends('historia_clinica_ids')
    def _compute_consulta_count(self):
        for dependiente in self:
            dependiente.consulta_count = len(dependiente.historia_clinica_ids)

    @api.depends('historia_psicologica_ids')
    def _compute_consulta_psicologica_count(self):
        for dependiente in self:
            dependiente.consulta_psicolociga_count = len(dependiente.historia_psicologica_ids)


    def action_view_historia_clinica(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Historial Clínico',
            'view_mode': 'tree,form',
            'res_model': 'mz.historia.clinica',
            'domain': [('dependiente_id', '=', self.id)],
            'context': dict(self.env.context, create=False)
        }
    
    def action_view_historia_clinica_psicologico(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Historial Psicológico',
            'view_mode': 'tree,form',
            'res_model': 'mz.historia.psicologica',
            'domain': [('dependiente_id', '=', self.id)],
            'context': dict(self.env.context, create=False)
        }
    
    
    @api.depends('fecha_nacimiento')
    def _compute_edad(self):
        for record in self:
            if record.fecha_nacimiento:
                hoy = date.today()
                diferencia = relativedelta(hoy, record.fecha_nacimiento)
                record.edad = f"{diferencia.years} años, {diferencia.months} meses, {diferencia.days} días"
            else:
                record.edad = "Sin fecha de nacimiento"

    @api.depends('primer_apellido', 'segundo_apellido', 'primer_nombre', 'segundo_nombre')
    def _compute_name(self):
        for record in self:
            parts = []
            if record.primer_apellido:
                parts.append(record.primer_apellido)
            if record.segundo_apellido:
                parts.append(record.segundo_apellido)
            if record.primer_nombre:
                parts.append(record.primer_nombre)
            if record.segundo_nombre:
                parts.append(record.segundo_nombre)
            
            record.name = ' '.join(parts)
    

    
    @api.onchange('tipo_documento', 'numero_documento')
    def _onchange_documento(self):
        if self.tipo_documento == 'dni' and self.numero_documento:
            if not utils.validar_cedula(self.numero_documento):
                return {'warning': {
                    'title': "Cédula Inválida",
                    'message': "El número de cédula ingresado no es válido."
                }}

    
