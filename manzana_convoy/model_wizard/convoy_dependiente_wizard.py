from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from datetime import date
from odoo.addons.manzana_de_cuidados import utils
from odoo.exceptions import UserError




class ConvoyBeneficiarioWizardDependiente(models.TransientModel):
    _name = 'mz_convoy.dependiente_wizard'
    _description = 'Dependiente en Wizard de Beneficiario'

    wizard_id = fields.Many2one('mz_convoy.beneficiario_wizard', string='Wizard')
    programa_id = fields.Many2one('pf.programas', string="Programa", readonly=True)
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
    servicio_ids = fields.Many2many('mz.asignacion.servicio', 'mz_convoy_dependiente_servicio_rel', 'dependiente_wizard_id', 'servicio_id', string='Servicios a Recibir', 
                                    domain="[('programa_id', '=', programa_id)]")


   
    @api.onchange('numero_documento')
    def _onchange_dependiente(self):
        if self.numero_documento:
            dependiente = self.env['mz.dependiente'].search([
                ('numero_documento', '=', self.numero_documento)
            ], limit=1)
            if dependiente:
                self._cargar_dependiente(dependiente)
            else:
                # Limpiar campos si no se encuentra el dependiente
                self._limpiar_campos()

    def _limpiar_campos(self):
        """Limpia todos los campos del dependiente"""
        self.update({
            'dependiente_id': False,
            'tipo_dependiente': False,
            'primer_apellido': False,
            'segundo_apellido': False,
            'primer_nombre': False,
            'segundo_nombre': False,
            'fecha_nacimiento': False,
            'tipo_documento': False,
            'servicio_ids': [(5, 0, 0)]  # Limpia los servicios seleccionados
        })
   

    def _cargar_dependiente(self, dependiente):
        """Carga los datos del dependiente encontrado"""
        self.update({
            'dependiente_id': dependiente.id,
            'tipo_dependiente': dependiente.tipo_dependiente.id,
            'primer_apellido': dependiente.primer_apellido,
            'segundo_apellido': dependiente.segundo_apellido,
            'primer_nombre': dependiente.primer_nombre,
            'segundo_nombre': dependiente.segundo_nombre,
            'fecha_nacimiento': dependiente.fecha_nacimiento,
            'tipo_documento': dependiente.tipo_documento,
            'numero_documento': dependiente.numero_documento,
            'servicio_ids': [(5, 0, 0)]  # Limpia los servicios al cargar nuevo dependiente
        })


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
    
