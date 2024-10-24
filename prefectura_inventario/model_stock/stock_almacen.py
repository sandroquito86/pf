from odoo import models, fields, api
from odoo.exceptions import ValidationError

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    programa_id = fields.Many2one('pf.programas', string='Programa Asociado', ondelete='restrict')
    adm = fields.Boolean(string='Administrador', compute='_compute_administrador_programa')
    code = fields.Char('Código', size=10)

    @api.depends('programa_id')
    def _compute_administrador_programa(self):
        for record in self:
            user = self.env.user
            record.adm = user.has_group('stock.group_stock_manager')

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if 'programa_id' in fields_list:
            user = self.env.user
            employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
            if employee and employee.programa_id:
                defaults['programa_id'] = employee.programa_id.id
        return defaults

    def filter_warehouses_by_program(self):
        action = {
            'name': 'Almacenes',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.warehouse',
            'view_mode': 'tree,form',
            'context': self.env.context,
        }
        if self.env.user.has_group('stock.group_stock_manager'):
            # Administrador: ve todos los almacenes
            return action
        elif self.env.user.has_group('prefectura_inventario.group_stock_program_manager'):
            # Administrador de programa: solo almacenes de su programa
            user_programa = self.env.user.employee_id.programa_id
            if user_programa:
                action['domain'] = [('programa_id', '=', user_programa.id)]
            else:
                action['domain'] = [('id', '=', False)]
        else:
            # Usuario regular: no ve almacenes (o ajusta según tus necesidades)
            action['domain'] = [('id', '=', False)]
        return action