from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date
from dateutil.relativedelta import relativedelta
from .. import utils

class PfEmployee(models.Model):
    _inherit = 'hr.employee'

    servicios_ids = fields.Many2many('mz.asignacion.servicio', string="Servicios Asignados")

    def _search(self, args, offset=0, limit=None, order=None, access_rights_uid=None):
        """
        Método _search personalizado para filtrar Empleados cuando viene el contexto
        """
        args = args or []
        user = self.env.user
        
        # Evitar recursión usando un contexto especial
        if not self._context.get('disable_custom_search'):
            valor = ''
            if self._context.get('filtrar_colaborador'):
                valor = 'externo'
            else:
                valor = 'interno'
            if self._context.get('filtrar_employee') or self._context.get('filtrar_colaborador'):                   
                # Verificar grupos
                if user.has_group('manzana_de_cuidados.group_beneficiario_manager'):
                    # Para coordinador: ver solo programas de módulo 2
                    programa_ids = self.with_context(disable_custom_search=True).search([
                        ('programa_id.modulo_id', '=', 2),('tipo_personal', '=', valor)
                    ]).ids
                    base_args = [('id', 'in', programa_ids)]
                
                elif user.has_group('manzana_de_cuidados.group_mz_registro_informacion') or \
                    user.has_group('manzana_de_cuidados.group_coordinador_manzana') or \
                    user.has_group('manzana_de_cuidados.group_manzana_lider_estrategia'):
                    # Para admin/asistente: ver servicios propios o creados por ellos
                    programa_ids = self.with_context(disable_custom_search=True).search([
                        ('programa_id', '=', user.programa_id.id),
                        ('tipo_personal', '=', valor)
                    ]).ids
                    base_args = [('id', 'in', programa_ids)]
                else:
                    employee_id = self.with_context(disable_custom_search=True).search([
                        ('user_id', '=', user.id)
                    ])
                    programa_ids = self.with_context(disable_custom_search=True).search([
                                    ('id', '=', employee_id.id),('tipo_personal', '=', valor)
                                ]).ids
                    base_args = [('id', 'in', programa_ids)]

                args = base_args + args

        return super(PfEmployee, self)._search(args, offset=offset, limit=limit, order=order, access_rights_uid=access_rights_uid)

    # def get_appropriate_view(self):
    #     # Obtener el usuario actual
    #     user = self.env.user
    #     employee_ids = []
    #     # Definir vistas por defecto (limitadas)
    #     if (user.has_group('manzana_de_cuidados.group_beneficiario_manager')):
    #         kanban_view = self.env.ref('manzana_de_cuidados.mz_hr_employee_kanban_view').id
    #         tree_view = self.env.ref('manzana_de_cuidados.view_mz_hr_employee_tree').id
    #         form_view = self.env.ref('manzana_de_cuidados.view_mz_hr_employee_form').id
    #         employee_ids = self.env['hr.employee'].search([('programa_id.modulo_id', '=', 2),('tipo_personal', '=', 'interno')]).ids

    #     elif user.has_group('manzana_de_cuidados.group_mz_registro_informacion'):

    #         kanban_view = self.env.ref('manzana_de_cuidados.mz_hr_employee_kanban_view').id
    #         tree_view = self.env.ref('manzana_de_cuidados.view_mz_hr_employee_tree').id
    #         form_view = self.env.ref('manzana_de_cuidados.view_mz_hr_employee_form').id
    #         employee_ids = self.env['hr.employee'].search([('programa_id', '=', user.programa_id.id),('tipo_personal', '=', 'interno')]).ids
            
    #     elif user.has_group('manzana_de_cuidados.group_coordinador_manzana') or \
    #         user.has_group('manzana_de_cuidados.group_manzana_lider_estrategia'):

    #         kanban_view = self.env.ref('manzana_de_cuidados.mz_hr_employee_kanban_view_read').id
    #         tree_view = self.env.ref('manzana_de_cuidados.view_mz_hr_employee_tree_limit').id
    #         form_view = self.env.ref('manzana_de_cuidados.view_mz_hr_employee_form_limit').id
    #         employee_ids = self.env['hr.employee'].search([('programa_id', '=', user.programa_id.id),('tipo_personal', '=', 'interno')]).ids
    #     else:
    #         kanban_view = self.env.ref('manzana_de_cuidados.mz_hr_employee_kanban_view_read').id
    #         tree_view = self.env.ref('manzana_de_cuidados.view_mz_hr_employee_tree_limit').id
    #         form_view = self.env.ref('manzana_de_cuidados.view_mz_hr_employee_form_limit').id
    #         employee_ids = self.env['hr.employee'].search([('user_id', '=', user.id),('tipo_personal', '=', 'interno')]).ids
            

    #     domain = [('id', 'in', employee_ids)]
    #     # Preparar la acción de ventana
    #     action = {
    #         'name': 'Empleados',
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'hr.employee',
    #         'view_mode': 'tree,form',
    #         'domain': domain,
    #         'views': [
    #             (kanban_view, 'kanban'),
    #             (tree_view, 'tree'),
    #             (form_view, 'form')
    #         ],
    #         'context': {
    #             'default_modulo_id': 2,
    #             'filtrar_programa': True
    #         },
    #         'target': 'current'
    #     }
        
    #     return action
    

    # def get_appropriate_colaborador_view(self):
    #     # Obtener el usuario actual
    #     user = self.env.user
    #     employee_ids = []
    #     # Definir vistas por defecto (limitadas)
    #     if (user.has_group('manzana_de_cuidados.group_beneficiario_manager')):
    #         kanban_view = self.env.ref('manzana_de_cuidados.view_mz_employee_kanban').id
    #         tree_view = self.env.ref('manzana_de_cuidados.view_mz_employee_tree').id
    #         form_view = self.env.ref('manzana_de_cuidados.view_mz_employee_form').id
    #         employee_ids = self.env['hr.employee'].search([('programa_id.modulo_id', '=', 2),('tipo_personal', '=', 'externo')]).ids

    #     elif user.has_group('manzana_de_cuidados.group_mz_registro_informacion'):

    #         kanban_view = self.env.ref('manzana_de_cuidados.view_mz_employee_kanban').id
    #         tree_view = self.env.ref('manzana_de_cuidados.view_mz_employee_tree').id
    #         form_view = self.env.ref('manzana_de_cuidados.view_mz_employee_form').id
    #         employee_ids = self.env['hr.employee'].search([('programa_id', '=', user.programa_id.id),('tipo_personal', '=', 'externo')]).ids
            
    #     elif user.has_group('manzana_de_cuidados.group_coordinador_manzana') or \
    #         user.has_group('manzana_de_cuidados.group_manzana_lider_estrategia'):

    #         kanban_view = self.env.ref('manzana_de_cuidados.view_mz_employee_kanban_limit').id
    #         tree_view = self.env.ref('manzana_de_cuidados.view_mz_employee_tree_limit').id
    #         form_view = self.env.ref('manzana_de_cuidados.view_mz_employee_form_limit').id
    #         employee_ids = self.env['hr.employee'].search([('programa_id', '=', user.programa_id.id),('tipo_personal', '=', 'externo')]).ids
    #     else:
    #         kanban_view = self.env.ref('manzana_de_cuidados.view_mz_employee_kanban_limit').id
    #         tree_view = self.env.ref('manzana_de_cuidados.view_mz_employee_tree_limit').id
    #         form_view = self.env.ref('manzana_de_cuidados.view_mz_employee_form_limit').id
    #         employee_ids = self.env['hr.employee'].search([('user_id', '=', user.id),('tipo_personal', '=', 'externo')]).ids

    #     domain = [('id', 'in', employee_ids)]
    #     # Preparar la acción de ventana
    #     action = {
    #         'name': 'Empleados',
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'hr.employee',
    #         'view_mode': 'tree,form',
    #         'domain': domain,
    #         'views': [
    #             (kanban_view, 'kanban'),
    #             (tree_view, 'tree'),
    #             (form_view, 'form')
    #         ],
    #         'context': {
    #             'default_modulo_id': 2,
    #             'filtrar_programa': True
    #         },
    #         'target': 'current'
    #     }
        
    #     return action