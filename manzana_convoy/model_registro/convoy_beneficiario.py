from odoo import models, fields, api
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError


class Beneficiario(models.Model):
    _inherit = 'mz.beneficiario'
    _description = 'Catálogo de Beneficiarios'

    num_documento = fields.Char('Número de Documento', required=True)
    nombres = fields.Char('Nombres', required=True)
    apellidos = fields.Char('Apellidos', required=True)
    es_extranjero = fields.Boolean('¿Es Migrante Extranjero?')
    pais = fields.Char('País', default='Ecuador')
    celular = fields.Char('Celular')
    operadora_id = fields.Many2one('mz.items', string='Operadora', domain=lambda self: [('catalogo_id', '=', self.env.ref('manzana_convoy.catalogo_operadoras').id)])
    # Campos de asistencia
    fecha_nacimiento = fields.Date('Fecha de Nacimiento')
    edad = fields.Integer('Edad', compute='_compute_edad', store=True)
    estado_civil_id = fields.Many2one('mz.items', string='Estado Civil', domain=lambda self: [('catalogo_id', '=', self.env.ref('manzana_convoy.catalogo_estado_civil').id)])
    genero_id = fields.Many2one('mz.items', string='Género', domain=lambda self: [('catalogo_id', '=', self.env.ref('manzana_convoy.catalogo_genero').id)])
    canton = fields.Char('Cantón')
    parroquia = fields.Char('Parroquia')
    direccion_domicilio = fields.Char('Dirección de domicilio')
    correo_electronico = fields.Char('Correo Electrónico')
    

    @api.onchange('tiene_discapacidad_hogar')
    def _onchange_tiene_discapacidad_hogar(self):
        if self.tiene_discapacidad_hogar == 'no':
            self.tipo_discapacidad_hogar_id = False
        elif self.tiene_discapacidad_hogar == 'si' and not self.tipo_discapacidad_hogar_id:
            # Buscar el registro "NINGUNA" por defecto
            ninguna = self.env['mz.items'].search([
                ('catalogo_id', '=', self.env.ref('manzana_convoy.catalogo_convoy_tipo_discapacidad').id),
                ('name', '=', 'NINGUNA')
            ], limit=1)
            if ninguna:
                self.tipo_discapacidad_hogar_id = ninguna.id 

    @api.onchange('mujeres_embarazadas', 'mujeres_embarazadas_chequeos', 'mujeres_embarazadas_menores')
    def _onchange_field(self):
        for record in self:            
            if record.mujeres_embarazadas_chequeos > record.mujeres_embarazadas:
                raise UserError('El número de mujeres embarazadas que asisten a chequeos no puede ser mayor al número total de mujeres embarazadas.')            
            if record.mujeres_embarazadas_menores > record.mujeres_embarazadas:
                raise UserError('El número de mujeres embarazadas menores de 18 años no puede ser mayor al número total de mujeres embarazadas.')

    @api.depends('fecha_nacimiento')
    def _compute_edad(self):
        for record in self:
            if record.fecha_nacimiento:
                today = date.today()
                record.edad = today.year - record.fecha_nacimiento.year - (
                    (today.month, today.day) < (record.fecha_nacimiento.month, record.fecha_nacimiento.day)
                )
            else:
                record.edad = 0

    _sql_constraints = [
        ('num_documento_uniq', 
         'UNIQUE(num_documento)',
         'Ya existe un beneficiario con este número de documento.')
    ]
