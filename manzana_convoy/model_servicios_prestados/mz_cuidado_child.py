from odoo import models, api
from odoo.exceptions import UserError


class ConvoyConsulta(models.Model):
    _inherit = 'mz.cuidado.child'
 
    
    @api.model
    def get_view(self, view_id=None, view_type='form', context=None, toolbar=False, submenu=False, **kwargs):
        context = context or {}
        user = self.env.user
        if user.has_group('manzana_convoy.group_mz_convoy_prestador_servicio') or \
           user.has_group('manzana_convoy.group_mz_convoy_administrador'):
            # Vistas completas para usuarios con permisos
            if view_type == 'tree':
                view_id = self.env.ref('manzana_de_cuidados.view_mz_cuidado_child_tree').id
            elif view_type == 'form':
                view_id = self.env.ref('manzana_de_cuidados.view_mz_cuidado_child_form').id
        else:
            # Vistas limitadas para usuarios sin permisos
            if view_type == 'tree':
                view_id = self.env.ref('manzana_de_cuidados.view_mz_cuidado_child_tree').id
            elif view_type == 'form':
                view_id = self.env.ref('manzana_de_cuidados.view_mz_cuidado_child_form_limit').id
        return super().get_view(view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu,**kwargs)