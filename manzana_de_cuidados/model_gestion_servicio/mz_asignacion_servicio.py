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
    servicio_domain_id = fields.Char(string='Domain Servicios',compute='_compute_author_domain_field')
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
    if_admin = fields.Boolean(string='Es administrador', default=False)
    get_sub_servicio= fields.Boolean(string='Tiene Subservicios', compute='_compute_get_sub_servicio', default=False)

    mostrar_boton_publicar = fields.Boolean(string='Mostrar Botón Publicar', compute='_compute_mostrar_boton_publicar')
    mostrar_bot_retirar_public = fields.Boolean(string='Mostrar Botón Retirar Publicar', compute='_compute_mostrar_bot_retirar_public')
    sub_servicio_ids = fields.Many2many('mz.sub.servicio', string='Sub Servicios',relation='asignacion_servicio_sub_servicio_rel')
    domain_sub_servicio_ids = fields.Char(string='Domain Sub servicios',compute='_compute_domain_sub_servicio_ids')
    

    @api.constrains('servicio_id', 'programa_id')
    def _check_unique_servicio_programa(self):
        for record in self:
            domain = [
                ('servicio_id', '=', record.servicio_id.id),
                ('programa_id', '=', record.programa_id.id),
                ('id', '!=', record.id)  # Excluir el registro actual
            ]
            if self.search_count(domain) > 0:
                raise UserError('Ya existe una asignación para este servicio en el programa seleccionado.')
            
    @api.constrains('personal_ids')
    def _check_personal_ids(self):
        for record in self:
            # Verificamos si el registro está siendo eliminado
            if not record._context.get('eliminar_registro') and not record.personal_ids:
                raise UserError("Por favor ingresar al menos un responsable")


    @api.depends('programa_id')
    def _compute_author_domain_field(self):
        for record in self:
            servicios_registrados = self.search([('programa_id', '=', record.programa_id.id), ('active', '=', True)]).mapped('servicio_id')
            if servicios_registrados:
                record.servicio_domain_id = [('id', 'not in', servicios_registrados.ids)]
            else:
                record.servicio_domain_id = [('id', '>', 0)]

    @api.depends('programa_id')
    def _compute_domain_personal_ids(self):
        for record in self:
            if record.programa_id:
                employees = self.env['hr.employee'].search([('programa_id', '=', [self.programa_id.id])])
                record.domain_personal_ids = [('id', 'in', employees.ids)]
            else:
                record.domain_personal_ids = [('id', 'in', [])]

    @api.depends('servicio_id')
    def _compute_domain_sub_servicio_ids(self):
        for record in self:
            if record.servicio_id:
                sub_servicios = self.env['mz.sub.servicio'].search([('id', 'in', self.servicio_id.sub_servicio_ids.ids)])
                record.domain_sub_servicio_ids = [('id', 'in', sub_servicios.ids)]
            else:
                record.domain_sub_servicio_ids = [('id', 'in', [])]

    @api.depends('servicio_id')
    def _compute_get_sub_servicio(self):
        for record in self:
            if record.servicio_id.sub_servicio_ids:
                record.get_sub_servicio = True
            else:
                record.get_sub_servicio = False

    @api.onchange('programa_id')
    def _onchange_programa_id(self):
        for record in self:
            record.servicio_id = False
            record.sub_servicio_ids = False
            record.personal_ids = False

    @api.onchange('servicio_id')
    def _onchange_servicio_id(self):
        for record in self:
            record.sub_servicio_ids = False
            record.personal_ids = False

    @api.onchange('programa_id')
    def _onchange_if_administrador(self):
        for record in self:
            groups = self.env.user.groups_id
            if self.env.ref('manzana_de_cuidados.group_beneficiario_manager') in groups or \
                self.env.ref('manzana_de_cuidados.group_manzana_lider_estrategia') in groups:
                record.if_admin = True
            else:
                record.if_admin = False


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

    @api.depends('name')
    def _compute_domain_programas(self):
        for record in self:
            groups = self.env.user.groups_id
            employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
            if self.env.ref('manzana_de_cuidados.group_manzana_lider_estrategia') in groups:
                record.domain_programa_id = ['|',('id', '=', employee_id.programa_id.id),('create_uid', '=', employee_id.user_id.id)]
            else:
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

    @api.model
    def create(self, vals):
        # Llamar al método create original
        record = super(AsignarServicio, self).create(vals)
        
        # Verificar si hay personal asignado
        if 'personal_ids' in vals:
            self._actualizar_servicios_empleados(vals['personal_ids'], record.id)
        
        return record

    def write(self, vals):        
        # Si se modifican los empleados
        if 'personal_ids' in vals:
            # Obtener los IDs de empleados antes y después de la modificación
            for record in self:
                # Obtener los IDs de empleados originales
                empleados_originales = record.personal_ids.ids
                result = super(AsignarServicio, self).write(vals)
                empleados_originales_pos = record.personal_ids.ids
                empleados_actualizados = []
                
                # Si se proporcionan nuevos empleados en vals
                nuevos_empleados = vals.get('personal_ids', [])
                
                # Determinar cambios
                if isinstance(nuevos_empleados[0], (list, tuple)):
                    # Manejar diferentes formatos de comandos de Odoo
                    if nuevos_empleados[0][0] in (0, 1, 2):  # Comandos de creación, actualización, borrado
                        # Convertir comandos a lista de IDs
                        empleados_actualizados = [
                            emp[1] if emp[0] in (1, 4) else emp[2]['id'] if emp[0] == 0 else None 
                            for emp in nuevos_empleados if emp[0] != 2
                        ]
                    else:
                        for emp in nuevos_empleados:
                            empleados_actualizados.append(emp[1])
                else:
                    empleados_actualizados = nuevos_empleados
            
                
                # Eliminar empleados que ya no están
                empleados_eliminados = set(empleados_originales) - set(empleados_originales_pos)
                # Actualizar servicios de empleados
                self._actualizar_servicios_empleados(
                    [(4, emp_id) for emp_id in empleados_actualizados], 
                    record.id
                )
                
                # Eliminar servicios de empleados que ya no están
                for emp_id in empleados_eliminados:
                    self._eliminar_servicio_empleado(emp_id, record.id)
        # Llamar al método write original
        result = super(AsignarServicio, self).write(vals)
        
        return result

    def _actualizar_servicios_empleados(self, personal_ids, servicio_id):
        """
        Método para agregar servicios a los empleados
        :param personal_ids: Lista de IDs de empleados
        :param servicio_id: ID del servicio a agregar
        """
        Employee = self.env['hr.employee']
        
        # Iterar sobre los empleados
        for comando in personal_ids:
            # Manejar diferentes tipos de comandos de Odoo
            if comando[0] == 4:  # Enlace de registro existente
                empleado = Employee.browse(comando[1])
                if empleado:
                    # Agregar el servicio al campo many2many
                    empleado.sudo().write({
                        'servicios_ids': [(4, servicio_id)]
                    })

    def _eliminar_servicio_empleado(self, empleado_id, servicio_id):
        """
        Método para eliminar un servicio de un empleado
        :param empleado_id: ID del empleado
        :param servicio_id: ID del servicio a eliminar
        """
        Employee = self.env['hr.employee']
        empleado = Employee.browse(empleado_id)
        
        if empleado:
            # Eliminar el servicio del campo many2many
            empleado.sudo().write({
                'servicios_ids': [(3, servicio_id)]
            })

    @api.model
    def get_view(self, view_id=None, view_type='form', context=None, toolbar=False, submenu=False, **kwargs):
        context = context or {}
        user = self.env.user

        if user.has_group('manzana_de_cuidados.group_manzana_lider_estrategia') or \
        user.has_group('manzana_de_cuidados.group_beneficiario_manager'):
            # Vistas completas para usuarios con permisos
            if view_type == 'tree':
                view_id = self.env.ref('manzana_de_cuidados.view_mz_asignacion_servicio_tree').id
            elif view_type == 'form':
                view_id = self.env.ref('manzana_de_cuidados.view_mz_asignacion_servicio_form').id
            elif view_type == 'kanban':
                view_id = self.env.ref('manzana_de_cuidados.mz_asignacion_servicio_kanban').id
        else:
            # Vistas limitadas para usuarios sin permisos
            if view_type == 'tree':
                view_id = self.env.ref('manzana_de_cuidados.view_mz_asignacion_servicio_tree_limit').id
            elif view_type == 'form':
                view_id = self.env.ref('manzana_de_cuidados.view_mz_asignacion_servicio_form_limit').id
            elif view_type == 'kanban':
                view_id = self.env.ref('manzana_de_cuidados.mz_asignacion_servicio_kanban_limit').id

        return super().get_view(
            view_id=view_id, 
            view_type=view_type, 
            context=context, 
            toolbar=toolbar, 
            submenu=submenu,
            **kwargs
        )
    

    def _search(self, args, offset=0, limit=None, order=None, access_rights_uid=None):
        """
        Método _search personalizado para filtrar programas cuando viene el contexto
        """
        args = args or []
        user = self.env.user
        
        # Evitar recursión usando un contexto especial
        if not self._context.get('disable_custom_search'):
            if self._context.get('filtrar_servicio'):                   
                # Verificar grupos
                if user.has_group('manzana_de_cuidados.group_beneficiario_manager'):
                    # Para coordinador: ver solo programas de módulo 2
                    programa_ids = self.with_context(disable_custom_search=True).search([
                        ('programa_id.modulo_id', '=', 2)
                    ]).ids
                    base_args = [('id', 'in', programa_ids)]
                
                elif user.has_group('manzana_de_cuidados.group_manzana_lider_estrategia'):
                    # Para admin/asistente: ver servicios propios o creados por ellos
                    programa_ids = self.with_context(disable_custom_search=True).search(['|', 
                        ('programa_id', '=', user.programa_id.id), 
                        ('programa_id.create_uid', '=', user.id)
                    ]).ids
                    base_args = [('id', 'in', programa_ids)]
                
                elif user.has_group('manzana_de_cuidados.group_coordinador_manzana')or \
                    user.has_group('manzana_de_cuidados.group_mz_registro_informacion'):
                    # Para usuarios sin rol especial: ver solo sus propios programas
                    programa_ids = self.with_context(disable_custom_search=True).search([
                        ('programa_id', '=', user.programa_id.id)
                    ]).ids
                    base_args = [('id', 'in', programa_ids)]
                else :
                    # Para usuarios sin rol especial: ver solo sus propios programas
                    programa_ids = self.with_context(disable_custom_search=True).search([
                        ('id', 'in', user.employee_id.servicios_ids.ids)
                    ]).ids
                    base_args = [('id', 'in', programa_ids)]

                args = base_args + args

        return super(AsignarServicio, self)._search(args, offset=offset, limit=limit, order=order, access_rights_uid=access_rights_uid)

    

    

class Pf_programas(models.Model):
    _inherit = 'pf.programas'
    _description = 'Programas'

    servicio_ids = fields.One2many('mz.asignacion.servicio', 'programa_id', string='Servicios')
    model_count_mz = fields.Integer(compute="_compute_model_count_mz", string="")

    mostrar_boton_publicar = fields.Boolean(string='Mostrar Botón Publicar', compute='_compute_mostrar_boton_publicar')
    mostrar_bot_retirar_public = fields.Boolean(string='Mostrar Botón Retirar Publicar', compute='_compute_mostrar_bot_retirar_public')
    servicios_text = fields.Char(string='Servicios Texto', compute='_compute_servicio_text')

    attachment_ids = fields.One2many('ir.attachment', 'res_id', string="Attachments")
    # To display in form view
    supported_attachment_ids = fields.Many2many(
        'ir.attachment', string="Subir Archivos", compute='_compute_supported_attachment_ids',
        inverse='_inverse_supported_attachment_ids')
    supported_attachment_ids_count = fields.Integer(compute='_compute_supported_attachment_ids')

    @api.depends('attachment_ids')
    def _compute_supported_attachment_ids(self):
        for holiday in self:
            holiday.supported_attachment_ids = holiday.attachment_ids
            holiday.supported_attachment_ids_count = len(holiday.attachment_ids.ids)


    def _inverse_supported_attachment_ids(self):
        for programa in self:
            programa.attachment_ids = programa.supported_attachment_ids

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

    @api.model
    def get_view(self, view_id=None, view_type='form', context=None, toolbar=False, submenu=False, **kwargs):
        context = context or {}
        user = self.env.user

        if user.has_group('manzana_de_cuidados.group_manzana_lider_estrategia') or \
        user.has_group('manzana_de_cuidados.group_beneficiario_manager'):
            # Vistas completas para usuarios con permisos
            if view_type == 'tree':
                view_id = self.env.ref('manzana_de_cuidados.view_mz_pf_programas_tree').id
            elif view_type == 'form':
                view_id = self.env.ref('manzana_de_cuidados.view_mz_pf_programas_form').id
            elif view_type == 'kanban':
                view_id = self.env.ref('manzana_de_cuidados.ma_pf_programas_view_kanban').id
        elif user.has_group('manzana_de_cuidados.group_coordinador_manzana')or \
            user.has_group('manzana_de_cuidados.group_mz_prestador_servicio') or \
            user.has_group('manzana_de_cuidados.group_mz_registro_informacion'):
            # Vistas limitadas para usuarios sin permisos
            if view_type == 'tree':
                view_id = self.env.ref('manzana_de_cuidados.view_mz_pf_programas_tree_limit').id
            elif view_type == 'form':
                view_id = self.env.ref('manzana_de_cuidados.view_mz_pf_programas_form_limit').id
            elif view_type == 'kanban':
                view_id = self.env.ref('manzana_de_cuidados.ma_pf_programas_view_kanban_limit').id

        return super().get_view(
            view_id=view_id, 
            view_type=view_type, 
            context=context, 
            toolbar=toolbar, 
            submenu=submenu,
            **kwargs
        )
    

    def _search(self, args, offset=0, limit=None, order=None, access_rights_uid=None):
        """
        Método _search personalizado para filtrar programas cuando viene el contexto
        """
        args = args or []
        user = self.env.user
        
        # Evitar recursión usando un contexto especial
        if not self._context.get('disable_custom_search'):
            if self._context.get('filtrar_programa'):                   
                # Verificar grupos
                if user.has_group('manzana_de_cuidados.group_beneficiario_manager'):
                    # Para coordinador: ver solo programas de módulo 2
                    programa_ids = self.with_context(disable_custom_search=True).search([
                        ('modulo_id', '=', 2)
                    ]).ids
                    base_args = [('id', 'in', programa_ids)]
                
                elif user.has_group('manzana_de_cuidados.group_manzana_lider_estrategia'):
                    # Para admin/asistente: ver servicios propios o creados por ellos
                    programa_ids = self.with_context(disable_custom_search=True).search(['|', 
                        ('id', '=', user.programa_id.id), 
                        ('create_uid', '=', user.id)
                    ]).ids
                    base_args = [('id', 'in', programa_ids)]
                
                else:
                    # Para usuarios sin rol especial: ver solo sus propios programas
                    programa_ids = self.with_context(disable_custom_search=True).search([
                        ('id', '=', user.programa_id.id)
                    ]).ids
                    base_args = [('id', 'in', programa_ids)]

                args = base_args + args

        return super(Pf_programas, self)._search(args, offset=offset, limit=limit, order=order, access_rights_uid=access_rights_uid)




   
