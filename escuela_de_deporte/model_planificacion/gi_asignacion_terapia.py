# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from string import ascii_letters, digits
import string


class AsignarTerapia(models.Model):
    _name = 'gi.asignacion.terapia'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Asignación de Terapia' 
    _rec_name = 'tipo_terapia_id'

    
    name = fields.Char(string='Nombre', required=True, compute='_compute_name', store=True)
    tipo_terapia_id = fields.Many2one(string='Terapia', comodel_name='gi.terapias', ondelete='restrict', required=True)  
    tipo_terapia_domain_id = fields.Char(string='Domain Servicios',compute='_compute_tipo_terapia_domain_id')
    image = fields.Binary(string='Imagen', attachment=True) 
    active = fields.Boolean(default=True, string='Activo', tracking=True)
    count_responsables = fields.Integer(compute="_compute_count_responsables", string="")
    personal_ids = fields.Many2many(string='Empleados Responsables', comodel_name='hr.employee', relation='gi_asignacion_terapia_items_employee_rel', 
                                      column1='asignacion_terapia_id', column2='empleado_id')
    domain_personal_ids = fields.Char(string='Domain Personal',compute='_compute_domain_personal_ids')
    

    programa_id = fields.Many2one('pf.programas', string='Centros', required=True, tracking=True, default=lambda self: self.env.programa_id)

    domain_programa_id = fields.Char(string='Domain Centros',compute='_compute_domain_programas')

    responsables_text = fields.Char(string='Responsables Texto', compute='_compute_responsables_text')

    if_publicado = fields.Boolean(string='Publicado', default=False)
    if_admin = fields.Boolean(string='Es administrador', default=False)

    mostrar_boton_publicar = fields.Boolean(string='Mostrar Botón Publicar', compute='_compute_mostrar_boton_publicar')
    mostrar_bot_retirar_public = fields.Boolean(string='Mostrar Botón Retirar Publicar', compute='_compute_mostrar_bot_retirar_public')
    

    @api.constrains('tipo_terapia_id', 'programa_id')
    def _check_unique_terapia_programa(self):
        for record in self:
            domain = [
                ('tipo_terapia_id', '=', record.tipo_terapia_id.id),
                ('programa_id', '=', record.programa_id.id),
                ('id', '!=', record.id)  # Excluir el registro actual
            ]
            if self.search_count(domain) > 0:
                raise UserError('Ya existe una asignación para este Tipo de Terapia en el Centro seleccionado.')
            
    @api.constrains('personal_ids')
    def _check_personal_ids(self):
        for record in self:
            # Verificamos si el registro está siendo eliminado
            if not record._context.get('eliminar_registro') and not record.personal_ids:
                raise UserError("Por favor registre al menos un responsable")


    @api.depends('programa_id')
    def _compute_tipo_terapia_domain_id(self):
        for record in self:
            terapias_registradas = self.search([('programa_id', '=', record.programa_id.id), ('active', '=', True)]).mapped('servicio_id')
            if terapias_registradas:
                record.tipo_terapia_domain_id = [('id', 'not in', terapias_registradas.ids)]
            else:
                record.tipo_terapia_domain_id = [('id', '>', 0)]

    @api.depends('programa_id')
    def _compute_domain_personal_ids(self):
        for record in self:
            if record.programa_id:
                employees = self.env['hr.employee'].search([('programa_id', '=', [self.programa_id.id])])
                record.domain_personal_ids = [('id', 'in', employees.ids)]
            else:
                record.domain_personal_ids = [('id', 'in', [])]

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
            if self.env.ref('guayas_integra.group_guayas_coordinador') in groups or \
                self.env.ref('guayas_integra.group_guayas_sistema') in groups:
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

    @api.depends('tipo_terapia_id', 'programa_id')
    def _compute_name(self):
        for record in self:
            if record.tipo_terapia_id and record.programa_id:
                record.name = f'{record.tipo_terapia_id.name} - {record.programa_id.name}'
            else:
                record.name = 'Asignación de Terapia'

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
            if self.env.ref('guayas_integra.group_guayas_coordinador') in groups:
                record.domain_programa_id = ['|',('id', '=', employee_id.programa_id.id),('create_uid', '=', employee_id.user_id.id)]
            else:
                programas = self.env['pf.programas'].search([('modulo_id', '=', self.env.ref('prefectura_base.modulo_1').id)])
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
            'res_model': 'confirm.publish.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_message': f'¿Está seguro de que desea retirar la publicación de la Terapia {self.name}? Esto sacara la Terapia del sitio web.', 'default_aux': 2}
        }

    def action_activar(self):
        for record in self:
            record.active = True
            # Lógica adicional para retirar el programa del sitio web

    @api.model
    def create(self, vals):
        # Llamar al método create original
        record = super(AsignarTerapia, self).create(vals)
        
        # Verificar si hay personal asignado
        if 'personal_ids' in vals:
            self._actualizar_terapias_empleados(vals['personal_ids'], record.tipo_terapia_id.id)
        
        return record

    def write(self, vals):        
        # Si se modifican los empleados
        if 'personal_ids' in vals:
            # Obtener los IDs de empleados antes y después de la modificación
            for record in self:
                # Obtener los IDs de empleados originales
                empleados_originales = record.personal_ids.ids
                result = super(AsignarTerapia, self).write(vals)
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
                self._actualizar_terapias_empleados(
                    [(4, emp_id) for emp_id in empleados_actualizados], 
                    record.tipo_terapia_id.id
                )
                
                # Eliminar servicios de empleados que ya no están
                for emp_id in empleados_eliminados:
                    self._eliminar_terapia_empleado(emp_id, record.tipo_terapia_id.id)
        # Llamar al método write original
        result = super(AsignarTerapia, self).write(vals)
        
        return result

    def _actualizar_terapias_empleados(self, personal_ids, tipo_terapia_id):
        """
        Método para agregar Terapias a los empleados
        :param personal_ids: Lista de IDs de empleados
        :param tipo_terapia_id: ID del la Terapia a agregar
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
                        'terapias_ids': [(4, tipo_terapia_id)]
                    })

    def _eliminar_terapia_empleado(self, empleado_id, tipo_terapia_id):
        """
        Método para eliminar una Terapia de un empleado
        :param empleado_id: ID del empleado
        :param tipo_terapia_id: ID del la terapia a eliminar
        """
        Employee = self.env['hr.employee']
        empleado = Employee.browse(empleado_id)
        
        if empleado:
            # Eliminar el servicio del campo many2many
            empleado.sudo().write({
                'terapias_ids': [(3, tipo_terapia_id)]
            })


    

    

