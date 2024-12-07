from odoo import models, fields, api
from odoo.exceptions import UserError
from string import ascii_letters, digits
import string

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




   
