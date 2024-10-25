from odoo import models, fields, api
from odoo.exceptions import ValidationError

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    programa_id = fields.Many2one('pf.programas', string='Programa Asociado', ondelete='restrict')
    code = fields.Char('Código', size=10)

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if 'programa_id' in fields_list:
            user = self.env.user
            employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
            if employee and employee.programa_id:
                defaults['programa_id'] = employee.programa_id.id
        return defaults


    def _search(self, args, offset=0, limit=None, order=None, access_rights_uid=None):
        if self._context.get('filtrar_programa'):
            # Aseguramos que args sea una lista antes de modificarla
            args = args if args else []
            # Agregamos el dominio para filtrar por programa
            if self.env.user.programa_id:
                args = [('programa_id', '=', self.env.user.programa_id.id)] + args
            else:
                # Si el usuario no tiene programa asignado, no mostramos ningún almacén
                args = [('id', '=', False)]  # Dominio que no retornará resultados
        
        return super()._search(args, offset=offset, limit=limit, order=order, access_rights_uid=access_rights_uid)

   