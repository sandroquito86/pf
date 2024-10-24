# -*- coding: utf-8 -*-

from odoo.exceptions import UserError
from odoo import models, fields, api
import re
from .. import utils

class Beneficiario(models.Model):
    _name = 'mz.beneficiario'
    _description = 'beneficiario que solicitan servicios'
    _inherits = {'pf.beneficiario': 'beneficiario_id'}
    _inherit = ['mail.thread', 'mail.activity.mixin']

    beneficiario_id = fields.Many2one('pf.beneficiario', string="Beneficiario", required=True, ondelete="cascade")
    dependientes_ids = fields.One2many('mz.dependiente', 'beneficiario_id', string='Dependientes')
    company_id = fields.Many2one('res.company', string='Compañía', required=True, default=lambda self: self.env.company)
    programa_id = fields.Many2one('pf.programas', string='Programa', required=True)
    
    historia_clinica_ids = fields.One2many('mz.historia.clinica', 'beneficiario_id', string='Historias Clínicas')
    consulta_count = fields.Integer(string='Número de Consultas', compute='_compute_consulta_count')
    aistencia_servicio_ids = fields.One2many('mz.asistencia_servicio', 'beneficiario_id', string='Servicios recibidos')
    asis_servicio_count = fields.Integer(string='Número de Servicios', compute='_compute_asis_servicios_count')

    @api.depends('historia_clinica_ids')
    def _compute_consulta_count(self):
        for beneficiario in self:
            beneficiario.consulta_count = len(beneficiario.historia_clinica_ids)

    @api.depends('aistencia_servicio_ids')
    def _compute_asis_servicios_count(self):
        for beneficiario in self:
             # Filtra los registros que están en el estado deseado
            estado = 'si'  # Reemplaza con el estado que deseas filtrar
            registros_filtrados = [registro for registro in beneficiario.aistencia_servicio_ids if registro.asistio == estado]
            beneficiario.asis_servicio_count = len(registros_filtrados)
    

    @api.onchange('email')
    def _onchange_email(self):
        """
        Validate the email format.
        """
        if self.email and not self._validar_email(self.email):
            return {
                'warning': {
                    'title': "Correo Electrónico Inválido",
                    'message': "El correo electrónico ingresado no es válido."
                }
            }
        
    @api.onchange('tipo_documento', 'numero_documento')
    def _onchange_documento(self):
        if self.tipo_documento == 'dni' and self.numero_documento:
            if not utils.validar_cedula(self.numero_documento):
                return {'warning': {
                    'title': "Cédula Inválida",
                    'message': "El número de cédula ingresado no es válido."
                }}

    
    

    def _validar_email(self, email):
        """
        Validate the email format using a regular expression.
        """
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_regex, email) is not None
    
    @api.constrains('numero_documento', 'tipo_documento')
    def _check_documento(self):
        for record in self:
            if record.tipo_documento == 'dni':
                if not utils.validar_cedula(record.numero_documento):
                    raise UserError("El número de cédula ingresado no es válido.")
                
    @api.model
    def create(self, vals):
        if self.env['mz.beneficiario'].search([('numero_documento', '=', vals.get('numero_documento'))]):
            raise UserError("Ya existe un beneficiario con esta identificación.")
        # Buscar si ya existe un beneficiario con el mismo número de documento
        numero_documento = vals.get('numero_documento')
        tipo_documento = vals.get('tipo_documento')
        
        if numero_documento and tipo_documento:
            existing_beneficiario = self.env['pf.beneficiario'].search([
                ('numero_documento', '=', numero_documento),
                ('tipo_documento', '=', tipo_documento)
            ], limit=1)
            
            if existing_beneficiario:
                # Si existe, usamos ese beneficiario en lugar de crear uno nuevo
                vals['beneficiario_id'] = existing_beneficiario.id
                # Actualizamos los campos del beneficiario existente
                existing_beneficiario.write({'programa_ids': [(4, vals['programa_id'])]})
            else:
                # Si no existe, creamos un nuevo beneficiario
                new_beneficiario = self.env['pf.beneficiario'].create({
                    k: v for k, v in vals.items() if k in self.env['pf.beneficiario']._fields
                })
                new_beneficiario.write({'programa_ids': [(4, vals['programa_id'])]})
                vals['beneficiario_id'] = new_beneficiario.id

        return super(Beneficiario, self).create(vals)
    
    def write(self, vals):
        if 'numero_documento' in vals:
            for record in self:
                if self.env['mz.beneficiario'].search([('numero_documento', '=', vals.get('numero_documento')), ('id', '!=', record.id)]):
                    raise UserError("Ya existe un beneficiario con esta identificación.")
        return super(Beneficiario, self).write(vals)

    @api.constrains('numero_documento', 'tipo_documento')
    def _check_unique_documento(self):
        for record in self:
            existing = self.search([
                ('numero_documento', '=', record.numero_documento),
                ('tipo_documento', '=', record.tipo_documento),
                ('id', '!=', record.id)
            ])
            if existing:
                raise UserError("Ya existe un beneficiario con este número y tipo de documento.")
    

    def crear_user(self):
        user_vals = {
            'name': self.name,
            'login': self.email,
            'email': self.email,
            'company_id': self.company_id.id,
            'company_ids': [(4, self.company_id.id)],
            'password': self.numero_documento,
            # 'groups_id': [(6, 0, [self.env.ref('prefectura_base.group_portal').id])]
        }
        user = self.env['res.users'].create(user_vals)
        self.user_id = user.id

    def action_view_historia_clinica(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Historial Clínico',
            'view_mode': 'tree,form',
            'res_model': 'mz.historia.clinica',
            'domain': [('beneficiario_id', '=', self.id)],
            'context': dict(self.env.context, create=False)
        }
    
    def action_view_asistencia_servicio(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Servicios Recibidos',
            'view_mode': 'tree,form',
            'res_model': 'mz.asistencia_servicio',
            'views': [
                (self.env.ref('manzana_de_cuidados.view_asistencia_servicio_benef_tree').id, 'tree'),
                (self.env.ref('manzana_de_cuidados.view_asistencia_servicio_benef_form').id, 'form')
            ],
            'search_view_id': self.env.ref('manzana_de_cuidados.view_asistencia_servicio_benef_search').id,
            'domain': [('beneficiario_id', '=', self.id), ('asistio', '=', 'si')],
            'context': dict(self.env.context, create=False)
        }
    

    

    