# -*- coding: utf-8 -*-

from odoo.exceptions import UserError
from odoo import models, fields, api
import re
from random import randint
from datetime import date
from dateutil.relativedelta import relativedelta


class MzMascota(models.Model):
    _name = 'mz.mascota'
    _description = 'Registro de Mascotas'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _get_especie_domain(self):
        catalogo_id = self.env.ref('prefectura_base.catalogo_especie').id
        return [('catalogo_id', '=', catalogo_id)]

    # Campos de identificación
    name = fields.Char(
        string='Nombre de la Mascota',
        required=True,
        tracking=True
    )
    codigo = fields.Char(
        string='Código de Identificación',
        required=True,
        copy=False,
        readonly=True,
        default='Nuevo'
    )
    
    # Relación con beneficiario
    beneficiario_id = fields.Many2one(
        'mz.beneficiario',
        string='Propietario',
        required=True,
        tracking=True
    )

    # Información básica
    especie_id = fields.Many2one(
        'pf.items',
        string='Especie',
        domain=_get_especie_domain,
        required=True,
        tracking=True
    )
    
    raza = fields.Char(
        string='Raza',
        tracking=True
    )
    
    sexo = fields.Selection([
        ('macho', 'Macho'),
        ('hembra', 'Hembra')
    ], string='Sexo', required=True, tracking=True)
    
    fecha_nacimiento = fields.Date(
        string='Fecha de Nacimiento',
        tracking=True
    )
    
    edad_aproximada = fields.Float(
        string='Edad Aproximada (Años)',
        tracking=True
    )
    
    color = fields.Char(
        string='Color/Señas Particulares',
        tracking=True
    )
    
    peso = fields.Float(
        string='Peso (kg)',
        tracking=True
    )

    # Estado reproductivo
    esterilizado = fields.Boolean(
        string='Esterilizado',
        tracking=True
    )
    
    fecha_esterilizacion = fields.Date(
        string='Fecha de Esterilización',
        tracking=True
    )

    # Estado de salud
    estado = fields.Selection([
        ('activo', 'Activo'),
        ('fallecido', 'Fallecido'),
        ('extraviado', 'Extraviado')
    ], string='Estado', default='activo', tracking=True)
    
    condicion_especial = fields.Text(
        string='Condiciones Especiales',
        help="Alergias, enfermedades crónicas, etc.",
        tracking=True
    )

    # Historial de vacunación
    ultima_vacunacion = fields.Date(
        string='Última Vacunación',
        tracking=True
    )
    
    ultima_desparasitacion = fields.Date(
        string='Última Desparasitación',
        tracking=True
    )

    # Campos de seguimiento
    active = fields.Boolean(
        default=True,
        tracking=True
    )
    
    notas = fields.Text(
        string='Notas Adicionales',
        tracking=True
    )

    @api.onchange('fecha_nacimiento', 'fecha_esterilizacion')
    def _onchange_fecha_esterilizacion(self):
        for record in self:
            if record.fecha_nacimiento and record.fecha_esterilizacion:
                if record.fecha_esterilizacion < record.fecha_nacimiento:
                    raise UserError('La fecha de esterilización no puede ser anterior a la fecha de nacimiento.')
                if record.fecha_esterilizacion > date.today():
                    raise UserError('La fecha de esterilización no puede ser posterior a la fecha actual.')
                
    @api.onchange('fecha_nacimiento')
    def _onchange_fecha_nacimiento(self):
        for record in self:
            if record.fecha_nacimiento:
                if record.fecha_nacimiento > date.today():
                    raise UserError('La fecha de nacimiento no puede ser posterior a la fecha actual.')
                record.edad_aproximada = relativedelta(date.today(), record.fecha_nacimiento).years

    @api.model
    def create(self, vals_list):
        if not vals_list.get('codigo') or vals_list.get('codigo') == 'Nuevo':
            # Obtén el nombre del registro
            name = vals_list.get('name', 'SinNombre').replace(' ', '_')
            
            # Obtén el beneficiario_id del diccionario de valores
            beneficiario = self.env['mz.beneficiario'].browse(vals_list.get('beneficiario_id', 0))
            
            # Inicializa las primeras letras de los apellidos
            letra_apellido_paterno = beneficiario.apellido_paterno[0].upper() if beneficiario.apellido_paterno else 'X'
            letra_apellido_materno = beneficiario.apellido_materno[0].upper() if beneficiario.apellido_materno else 'X'
            
            # Genera el código a partir del nombre y las letras de los apellidos
            vals_list['codigo'] = f"{name}-{letra_apellido_paterno}{letra_apellido_materno}"
    
        # Llama al método 'create' del modelo original para crear los registros
        return super(MzMascota, self).create(vals_list)
    
    def write(self, vals):
        if 'name' in vals:  # Si el campo 'name' se modifica
            for record in self:
                # Reemplaza espacios con guiones bajos
                name = vals.get('name', record.name).replace(' ', '_')
                
                # Verifica si hay un 'beneficiario_id' en los valores o usa el actual
                beneficiario_id = vals.get('beneficiario_id', record.beneficiario_id.id)
                beneficiario = self.env['mz.beneficiario'].browse(beneficiario_id)
                
                # Obtén las iniciales de los apellidos del beneficiario
                letra_apellido_paterno = beneficiario.apellido_paterno[0].upper() if beneficiario.apellido_paterno else 'X'
                letra_apellido_materno = beneficiario.apellido_materno[0].upper() if beneficiario.apellido_materno else 'X'
                
                # Actualiza el código basado en el nuevo 'name'
                vals['codigo'] = f"{name}-{letra_apellido_paterno}{letra_apellido_materno}"
        
        # Llama al método 'write' del modelo original
        return super(MzMascota, self).write(vals)