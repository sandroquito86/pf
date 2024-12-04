from odoo import models, api
from odoo.exceptions import UserError


class MzConvoyVeterinaria(models.Model):
    _inherit = 'mz.servicio.veterinario'
 
    @api.model
    def get_view(self, view_id=None, view_type='form', context=None, toolbar=False, submenu=False, **kwargs):
        context = context or {}
        user = self.env.user
        if user.has_group('manzana_convoy.group_mz_convoy_prestador_servicio') or \
           user.has_group('manzana_convoy.group_mz_convoy_administrador'):
            # Vistas completas para usuarios con permisos
            if view_type == 'tree':
                view_id = self.env.ref('manzana_de_cuidados.view_mz_servicio_veterinario_tree').id
            elif view_type == 'form':
                view_id = self.env.ref('manzana_de_cuidados.view_mz_servicio_veterinario_form').id
        else:
            # Vistas limitadas para usuarios sin permisos
            if view_type == 'tree':
                view_id = self.env.ref('manzana_de_cuidados.view_mz_servicio_veterinario_tree').id
            elif view_type == 'form':
                view_id = self.env.ref('manzana_de_cuidados.view_mz_servicio_veterinario_form_read').id


        return super().get_view(
            view_id=view_id, 
            view_type=view_type, 
            context=context, 
            toolbar=toolbar, 
            submenu=submenu,
            **kwargs
        )
    
    def _search(self, args, offset=0, limit=None, order=None, access_rights_uid=None):
        args = args or []
        user = self.env.user
        base_args = [('id', 'in', [])]

        if not self._context.get('disable_custom_search'):
            if self._context.get('filtrar_convoy'):
                if user.has_group('manzana_convoy.group_mz_convoy_administrador'):
                    programa_ids = self.with_context(disable_custom_search=True).search([
                        ('programa_id.modulo_id', '=', 4)
                    ]).ids
                    base_args = [('id', 'in', programa_ids)]
                elif user.has_group('manzana_convoy.group_mz_convoy_prestador_servicio') or \
                    user.has_group('manzana_convoy.group_mz_convoy_coordinador'):
                    if_consulta = False
                    for servicio in user.employee_id.servicios_ids:
                        if servicio.servicio_id.tipo_servicio == 'consulta_psicologica':
                            if_consulta = True
                            break
                    if if_consulta:
                        employee_id = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
                        programa_ids = self.with_context(disable_custom_search=True).search([
                            '|',
                            '&',
                            ('programa_id', '=', user.programa_id.id),
                            ('state', '=', 'finalizado'),
                            ('personal_id', '=', employee_id.id)
                        ]).ids
                        base_args = [('id', 'in', programa_ids)]

        args = base_args + args
        return super(MzConvoyVeterinaria, self)._search(
            args, offset=offset, limit=limit, order=order, access_rights_uid=access_rights_uid
        )
    