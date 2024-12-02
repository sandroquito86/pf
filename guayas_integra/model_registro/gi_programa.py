# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from string import ascii_letters, digits
import string

class Pf_programas(models.Model):
    _inherit = 'pf.programas'
    _description = 'Programas'

    terapia_ids = fields.One2many('gi.asignacion.terapia', 'programa_id', string='Terapias')
    model_count = fields.Integer(compute="_compute_model_count", string="")
    terapia_text = fields.Char(string='Terapia Texto', compute='_compute_terapia_text')


    @api.depends('model_count')
    def _compute_terapia_text(self):
        for record in self:
            if record.model_count == 1:
                record.serviciosterapia_texttext = "1 Tipo de Terapia"
            else:
                record.terapia_text = f"{record.model_count} Tipos de Terapias"


    @api.depends('terapia_ids')
    def _compute_model_count(self):
        model_data = self.env['gi.asignacion.terapia']._read_group([
            ('programa_id', 'in', self.ids),
        ], ['programa_id'], ['__count'])
        models_brand = {brand.id: count for brand, count in model_data}
        for record in self:
            record.model_count = models_brand.get(record.id, 0)

    def action_publish_wizard(self):
        # Abrir el wizard de confirmación
        return {
            'type': 'ir.actions.act_window',
            'name': 'Confirmar Retiro de Publicación',
            'res_model': 'confirm.publish.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_message': f'¿Está seguro de que desea retirar la publicación del Programa {self.name}? Esto sacara el programa del sitio web.', 'default_aux': 2}
        }
    
    def action_brand_model_terapia(self):
        self.ensure_one()
        view = {
            'type': 'ir.actions.act_window',
            'view_mode': 'kanban,tree,form',
            'res_model': 'gi.asignacion.terapia',
            'name': 'Terapias',
            'context': {'search_default_programa_id': self.id, 'default_programa_id': self.id}
        }

        return view
    
    @api.model
    def get_view(self, view_id=None, view_type='form', context=None, toolbar=False, submenu=False, **kwargs):
        context = context or {}
        user = self.env.user

        if user.has_group('guayas_integra.group_guayas_sistema') or \
            user.has_group('guayas_integra.group_guayas_coordinador'):
            if view_type == 'tree':
                view_id = self.env.ref('guayas_integra.view_gi_pf_programas_tree').id
            elif view_type == 'form':
                view_id = self.env.ref('guayas_integra.view_gi_pf_programas_form').id
            elif view_type == 'kanban':
                view_id = self.env.ref('guayas_integra.gi_pf_programas_view_kanban').id
        else:
            if view_type == 'tree':
                view_id = self.env.ref('guayas_integra.view_gi_pf_programas_tree_limit').id
            elif view_type == 'form':
                view_id = self.env.ref('guayas_integra.view_gi_pf_programas_form_limit').id
            elif view_type == 'kanban':
                view_id = self.env.ref('guayas_integra.gi_pf_programas_view_kanban_limit').id

        return super().get_view(
            view_id=view_id, 
            view_type=view_type, 
            context=context, 
            toolbar=toolbar, 
            submenu=submenu,
            **kwargs
        )
    
    
    @api.model
    def _search(self, args, offset=0, limit=None, order=None, access_rights_uid=None):
        # Evitar recursión
        args = args or []
        user = self.env.user
        base_args = [('id', '>', 0)]
        if not self._context.get('disable_custom_search'):
            if self._context.get('filtrar_programa_gi'): 
                # Tu lógica adicional
                if user.has_group('guayas_integra.group_guayas_sistema'):
                    # Para coordinador: ver solo programas de módulo 2
                    programa_ids = self.with_context(disable_custom_search=True).search([
                        ('modulo_id', '=', 1)
                    ]).ids
                    base_args = [('id', 'in', programa_ids)]
                
                elif user.has_group('guayas_integra.group_guayas_coordinador'):
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
        
        # Llamar al método original
        return super(Pf_programas, self)._search(
            args, offset=offset, limit=limit, order=order, 
            access_rights_uid=access_rights_uid
        )