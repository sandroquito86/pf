from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from datetime import date
from odoo.addons.manzana_de_cuidados import utils
from odoo.exceptions import UserError




class ConvoyBeneficiarioWizardDependiente(models.TransientModel):
    _name = 'mz_convoy.dependiente_wizard'
    _description = 'Dependiente en Wizard de Beneficiario'

    wizard_id = fields.Many2one('mz_convoy.beneficiario_wizard', string='Wizard')
    name = fields.Char(string='Nombre Completo', compute='_compute_name', store=True)
    dependiente_id = fields.Many2one('mz.dependiente', string='Dependiente')  # Agregamos este campo
    tipo_dependiente = fields.Many2one('pf.items', string="Tipo de Dependiente", required=True,
        domain=lambda self: [('catalogo_id', '=', self.env.ref('prefectura_base.tipo_dependiente').id)])
    primer_apellido = fields.Char(string='Primer Apellido', required=True)
    segundo_apellido = fields.Char(string='Segundo Apellido')
    primer_nombre = fields.Char(string='Primer Nombre', required=True)
    segundo_nombre = fields.Char(string='Segundo Nombre')
    fecha_nacimiento = fields.Date(string='Fecha de Nacimiento')
    tipo_documento = fields.Selection([('dni', 'DNI'), ('pasaporte', 'Pasaporte'), ('carnet_extranjeria', 'Carnet de Extranjería')], string='Tipo de Documento', required=True)
    numero_documento = fields.Char(string='Número de Documento', required=True)
    edad = fields.Char(string="Edad", compute="_compute_edad", store=True)

   

    @api.onchange('numero_documento')
    def _onchange_dependiente(self):
        if self.numero_documento:
            dependiente = self.env['mz.dependiente'].search([
                ('numero_documento', '=', self.numero_documento)
            ], limit=1)
            if dependiente:
                self._cargar_dependiente(dependiente)

    def _cargar_dependiente(self, dependiente):
        """Carga los datos del dependiente encontrado"""
        self.dependiente_id = dependiente.id
        self.tipo_dependiente = dependiente.tipo_dependiente.id
        self.primer_apellido = dependiente.primer_apellido
        self.segundo_apellido = dependiente.segundo_apellido
        self.primer_nombre = dependiente.primer_nombre
        self.segundo_nombre = dependiente.segundo_nombre
        self.fecha_nacimiento = dependiente.fecha_nacimiento
        self.tipo_documento = dependiente.tipo_documento
        self.numero_documento = dependiente.numero_documento

    @api.onchange('tipo_documento', 'numero_documento')
    def _onchange_documento(self):
        if self.tipo_documento == 'dni' and self.numero_documento:
            if not utils.validar_cedula(self.numero_documento):
                return {
                    'warning': {
                        'title': "Cédula Inválida",
                        'message': "El número de cédula ingresado no es válido."
                    }
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

    @api.onchange('numero_documento')
    def _onchange_dependiente(self):
        if self.numero_documento:
            dependiente = self.env['mz.dependiente'].search([
                ('numero_documento', '=', self.numero_documento)
            ], limit=1)
            if dependiente:
                self._cargar_dependiente(dependiente)

    def _cargar_dependiente(self, dependiente):
        """Carga los datos del dependiente encontrado"""
        self.dependiente_id = dependiente.id
        self.tipo_dependiente = dependiente.tipo_dependiente.id
        self.primer_apellido = dependiente.primer_apellido
        self.segundo_apellido = dependiente.segundo_apellido
        self.primer_nombre = dependiente.primer_nombre
        self.segundo_nombre = dependiente.segundo_nombre
        self.fecha_nacimiento = dependiente.fecha_nacimiento
        self.tipo_documento = dependiente.tipo_documento
        self.numero_documento = dependiente.numero_documento

    @api.onchange('tipo_documento', 'numero_documento')
    def _onchange_documento(self):
        if self.tipo_documento == 'dni' and self.numero_documento:
            if not utils.validar_cedula(self.numero_documento):
                return {
                    'warning': {
                        'title': "Cédula Inválida",
                        'message': "El número de cédula ingresado no es válido."
                    }
                }

    def _prepare_dependiente_values(self):
        """Prepara los valores para crear/actualizar el dependiente"""
        return {
            'tipo_dependiente': self.tipo_dependiente.id,
            'primer_apellido': self.primer_apellido,
            'segundo_apellido': self.segundo_apellido,
            'primer_nombre': self.primer_nombre,
            'segundo_nombre': self.segundo_nombre,
            'fecha_nacimiento': self.fecha_nacimiento,
            'tipo_documento': self.tipo_documento,
            'numero_documento': self.numero_documento,
            'beneficiario_id': self.wizard_id.beneficiario_id.id,
        }

    def _prepare_convoy_dependiente_values(self, dependiente):
        """Prepara los valores para la relación convoy-dependiente"""
        return {
            'convoy_id': self.wizard_id.convoy_id.id,
            'beneficiario_id': self.wizard_id.beneficiario_id.id,
            'dependiente_id': dependiente.id,
            'tipo_registro': self.wizard_id.tipo_registro,
            'fecha_registro': fields.Datetime.now(),
            'tipo_beneficiario': 'dependiente',
        }
    
