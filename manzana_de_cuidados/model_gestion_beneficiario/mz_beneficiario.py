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
    historia_psicologica_ids = fields.One2many('mz.historia.psicologica', 'beneficiario_id', string='Historias Psicológicas')
    consulta_psicologica_count = fields.Integer(string='Número de Consultas Psicológicas', compute='_compute_consulta_psicologica_count')
    aistencia_servicio_ids = fields.One2many('mz.asistencia_servicio', 'beneficiario_id', string='Servicios recibidos')
    asis_servicio_count = fields.Integer(string='Número de Servicios', compute='_compute_asis_servicios_count')

    autoriza_consentimiento = fields.Boolean(string='Autoriza Consentimiento de Datos Socioeconómicos', default=False)
    file = fields.Binary(string='Archivo', attachment=True)
    name_file = fields.Char(string='Nombre de Archivo')

    # datos socioeconomicos
    tiene_discapacidad = fields.Boolean('¿Tiene usted alguna discapacidad?')
    recibe_bono = fields.Boolean('¿Recibe algún tipo de bono?')
    tipo_discapacidad_id = fields.Many2one('pf.items', string='Tipo de Discapacidad', 
                                           domain=lambda self: [('catalogo_id', '=', self.env.ref('prefectura_base.tipos_discapacidad').id)])
    nivel_instruccion_id = fields.Many2one('pf.items', string='Nivel de Instrucción',
                                           domain=lambda self: [('catalogo_id', '=', self.env.ref('prefectura_base.catalogo_nivel_instruccion').id)])
    situacion_laboral_id = fields.Many2one('pf.items', string='Situación Laboral',
                                           domain=lambda self: [('catalogo_id', '=', self.env.ref('prefectura_base.catalogo_situacion_laboral').id)])
    tipo_vivienda_id = fields.Many2one('pf.items', string='La vivienda donde habita es?', 
                                       domain=lambda self: [('catalogo_id', '=', self.env.ref('prefectura_base.catalogo_tipo_vivienda').id)])
    tiene_internet = fields.Selection([('si', 'SI'), ('no', 'NO')], string='¿Su hogar cuenta con internet?')
    tiene_agua_potable = fields.Selection([('si', 'SI'), ('no', 'NO')], string='¿La vivienda donde habita tiene servicio de agua potable por tubería?')
    tiene_luz_electrica = fields.Selection([('si', 'SI'), ('no', 'NO')], string='¿La vivienda donde habita cuenta con luz eléctrica?')
    tiene_alcantarillado = fields.Selection([('si', 'SI'), ('no', 'NO')], string='¿La vivienda donde habita tiene servicio de alcantarillado?')
    es_cuidador = fields.Selection([('si', 'SI'), ('no', 'NO')], string='¿Es cuidador/a?')
    hora_tarea_domestica = fields.Integer(string='Horas a tareas domésticas',)
    sostiene_hogar = fields.Selection([('si', 'SI'), ('no', 'NO')], string='¿Usted sostiene económicamente su hogar?')
    enfermedad_catastrofica = fields.Selection([('si', 'SI'), ('no', 'NO')], string='¿Padece alguna enfermedad catastrófica?')
    hombres_hogar = fields.Integer(string='¿Cuántos hombres viven en el hogar(contando niños)?',)
    mujer_hogar = fields.Integer(string='¿Cuántos mujeres viven en el hogar(contando niñas)?',)
    ninos_menores = fields.Integer(string='¿Cuántos niños menores de edad habitan en el hogar?',)
    ninos_5_estudiando = fields.Integer(string='¿Cuántos niños mayores de 5 años que habitan en el hogar estan estudiando?',)
    mujeres_embarazadas = fields.Integer(string='¿Cuántas mujeres embarazadas habitan en su hogar?', default=0)
    mujeres_embarazadas_chequeos = fields.Integer(string='¿Cuántas mujeres embarazadas que habitan en el hogar asisten a chequeos médicos?', default=0)
    mujeres_embarazadas_menores = fields.Integer(string='¿Cuántas de las mujeres embarazadas son menores de 18 años?', default=0)
    mayor_65 = fields.Selection([('si', 'SI'), ('no', 'NO')], string='¿Hay mayores de 65 años viviendo en su hogar?')
    discapacidad_hogar = fields.Selection([('si', 'SI'), ('no', 'NO')], string='¿Hay personas con discapacidad viviendo en su hogar?')
    tiene_discapacidad_hogar = fields.Selection([('si', 'SI'),('no', 'NO')], string='¿Hay personas con discapacidad viviendo en su hogar?', default='no')
    tipo_discapacidad_hogar_id = fields.Many2one('pf.items', string='¿Qué tipo de discapacidad tiene?',
                                                 domain=lambda self: [('catalogo_id', '=', self.env.ref('prefectura_base.tipos_discapacidad').id)])   


    @api.depends('historia_clinica_ids')
    def _compute_consulta_count(self):
        for beneficiario in self:
            beneficiario.consulta_count = len(beneficiario.historia_clinica_ids)

    @api.depends('historia_psicologica_ids')
    def _compute_consulta_psicologica_count(self):
        for beneficiario in self:
            beneficiario.consulta_psicologica_count = len(beneficiario.historia_psicologica_ids)

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
    
    def action_view_historia_clinica_psicologico(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Historial Psicológico',
            'view_mode': 'tree,form',
            'res_model': 'mz.historia.psicologica',
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
    

    

    