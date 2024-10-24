# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from string import ascii_letters, digits
import string


class AsignarServicio(models.Model):
    _name = 'mz.asignacion.servicio'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Asignación de Servicios' 
    _rec_name = 'servicio_id'

    
    name = fields.Char(string='Nombre', required=True, compute='_compute_name', store=True)
    servicio_id = fields.Many2one(string='Servicio', comodel_name='mz.servicio', ondelete='restrict', required=True)  
    image = fields.Binary(string='Imagen', attachment=True) 
    active = fields.Boolean(default=True, string='Activo', tracking=True)
    count_responsables = fields.Integer(compute="_compute_count_responsables", string="")
    personal_ids = fields.Many2many(string='Empleados Responsables', comodel_name='hr.employee', relation='mz_asignacion_servicio_items_employee_rel', 
                                      column1='asignacion_servicio_id', column2='empleado_id')
    domain_personal_ids = fields.Char(string='Domain Personal',compute='_compute_domain_personal_ids')
                                      
                             #borrar comentario
    
    # servicio_domain_id = fields.Char(string='Domain Servicios',compute='_compute_author_domain_field')
    

    programa_id = fields.Many2one('pf.programas', string='Programa', required=True, tracking=True, default=lambda self: self.env.programa_id)

    domain_programa_id = fields.Char(string='Domain Programa',compute='_compute_domain_programas')

    responsables_text = fields.Char(string='Responsables Texto', compute='_compute_responsables_text')

    if_publicado = fields.Boolean(string='Publicado', default=False)

    mostrar_boton_publicar = fields.Boolean(string='Mostrar Botón Publicar', compute='_compute_mostrar_boton_publicar')
    mostrar_bot_retirar_public = fields.Boolean(string='Mostrar Botón Retirar Publicar', compute='_compute_mostrar_bot_retirar_public')

    @api.constrains('name', 'programa_id')
    def _check_name_unique_per_programa(self):
        for record in self:
            domain = [
                ('name', '=', record.name),
                ('programa_id', '=', record.programa_id.id),
                ('id', '!=', record.id),  # Excluye el registro actual para permitir actualizaciones
            ]
            if self.search_count(domain) > 0:
                raise UserError("El servicio no puede estar duplicado en el mismo programa.")

    @api.depends('programa_id')
    def _compute_domain_personal_ids(self):
        for record in self:
            if record.programa_id:
                employees = self.env['hr.employee'].search([('programa_id', '=', [self.programa_id.id])])
                record.domain_personal_ids = [('id', 'in', employees.ids)]
            else:
                record.domain_personal_ids = [('id', 'in', [])]

    @api.depends('active', 'if_publicado')
    def _compute_mostrar_boton_publicar(self):
        for record in self:
            if not record.if_publicado and record.active:
                record.mostrar_boton_publicar = True
            else:
                record.mostrar_boton_publicar = False

    @api.depends('active', 'if_publicado')
    def _compute_mostrar_bot_retirar_public(self):
        for record in self:
            if record.if_publicado and record.active:
                record.mostrar_bot_retirar_public = True
            else:
                record.mostrar_bot_retirar_public = False

    @api.depends('servicio_id', 'programa_id')
    def _compute_name(self):
        for record in self:
            if record.servicio_id and record.programa_id:
                record.name = f'{record.servicio_id.name} - {record.programa_id.name}'
            else:
                record.name = 'Asignación de Servicio'

    @api.depends('count_responsables')
    def _compute_responsables_text(self):
        for record in self:
            if record.count_responsables == 1:
                record.responsables_text = "1 Responsable"
            else:
                record.responsables_text = f"{record.count_responsables} Responsables"

    @api.depends('personal_ids')
    def _compute_count_responsables(self):
        for record in self:
            if record.personal_ids:
                record.count_responsables = len(record.personal_ids) 
            else:
                record.count_responsables = 0

    @api.depends('servicio_id')
    def _compute_domain_programas(self):
        for record in self:
            programas = self.env['pf.programas'].search([('modulo_id', '=', self.env.ref('prefectura_base.modulo_2').id)])
            if programas:
                record.domain_programa_id = [('id', 'in', programas.ids)]
            else:
                record.domain_programa_id = [('id', 'in', [])]
    
    def action_publish(self):
        for record in self:
            record.if_publicado = True
            # Lógica adicional para publicar el programa en el sitio web

    def action_unpublish(self):
        for record in self:
            record.if_publicado = False
            record.active = False
            # Lógica adicional para retirar el programa del sitio web

    def action_unpublish_wizard(self):
        # Abrir el wizard de confirmación
        return {
            'type': 'ir.actions.act_window',
            'name': 'Confirmar Retiro de Publicación',
            'res_model': 'confirm.unpublish.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_message': f'¿Está seguro de que desea retirar la publicación del Servicio {self.name}? Esto sacara el Servicio del sitio web.', 'default_aux': 2}
        }

    def action_activar(self):
        for record in self:
            record.active = True
            # Lógica adicional para retirar el programa del sitio web

    

class Pf_programas(models.Model):
    _inherit = 'pf.programas'
    _description = 'Programas'

    servicio_ids = fields.One2many('mz.asignacion.servicio', 'programa_id', string='Servicios')
    model_count_mz = fields.Integer(compute="_compute_model_count_mz", string="")

    mostrar_boton_publicar = fields.Boolean(string='Mostrar Botón Publicar', compute='_compute_mostrar_boton_publicar')
    mostrar_bot_retirar_public = fields.Boolean(string='Mostrar Botón Retirar Publicar', compute='_compute_mostrar_bot_retirar_public')
    servicios_text = fields.Char(string='Servicios Texto', compute='_compute_servicio_text')

    @api.depends('model_count_mz')
    def _compute_servicio_text(self):
        for record in self:
            if record.model_count_mz == 1:
                record.servicios_text = "1 Servicio"
            else:
                record.servicios_text = f"{record.model_count_mz} Servicios"

    @api.depends('active', 'if_publicado')
    def _compute_mostrar_boton_publicar(self):
        for record in self:
            if not record.if_publicado and record.active:
                record.mostrar_boton_publicar = True
            else:
                record.mostrar_boton_publicar = False

    @api.depends('active', 'if_publicado')
    def _compute_mostrar_bot_retirar_public(self):
        for record in self:
            if record.if_publicado and record.active:
                record.mostrar_bot_retirar_public = True
            else:
                record.mostrar_bot_retirar_public = False


    @api.depends('servicio_ids')
    def _compute_model_count_mz(self):
        model_data = self.env['mz.asignacion.servicio']._read_group([
            ('programa_id', 'in', self.ids),
        ], ['programa_id'], ['__count'])
        models_brand = {brand.id: count for brand, count in model_data}
        for record in self:
            record.model_count_mz = models_brand.get(record.id, 0)

    def action_brand_model(self):
        self.ensure_one()
        view = {
            'type': 'ir.actions.act_window',
            'view_mode': 'kanban,tree,form',
            'res_model': 'mz.asignacion.servicio',
            'name': 'Servicios',
            'context': {'search_default_programa_id': self.id, 'default_programa_id': self.id}
        }

        return view
    
    def action_publish(self):
        for record in self:
            record.if_publicado = True
            # Lógica adicional para publicar el programa en el sitio web

    def action_unpublish(self):
        for record in self:
            record.if_publicado = False
            record.active = False
            # Lógica adicional para retirar el programa del sitio web

    def action_unpublish_wizard(self):
        # Abrir el wizard de confirmación
        return {
            'type': 'ir.actions.act_window',
            'name': 'Confirmar Retiro de Publicación',
            'res_model': 'confirm.unpublish.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_message': f'¿Está seguro de que desea retirar la publicación del Programa {self.name}? Esto sacara el programa del sitio web.', 'default_aux': 2}
        }

    def action_activar(self):
        for record in self:
            record.active = True
            # Lógica adicional para retirar el programa del sitio web



   
