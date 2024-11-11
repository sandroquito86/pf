from odoo import models, fields, api
from odoo.exceptions import ValidationError

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    programa_id = fields.Many2one('pf.programas', string='Programa Asociado', related='warehouse_id.programa_id', store=True)
    adm = fields.Boolean(string='Administrador', compute='_compute_administrador')
    warehouse_id_domain = fields.Char(compute="_compute_warehouse_id_domain", readonly=True, store=False)

    @api.depends('programa_id')
    def _compute_administrador(self):
        for record in self:
            record.adm = self.env.user.has_group('stock.group_stock_manager')

    @api.depends('programa_id')
    def _compute_warehouse_id_domain(self):
        for record in self:
            if self.env.user.has_group('stock.group_stock_manager'):
                if not record.programa_id:
                    # Si no se selecciona programa, mostrar almacenes sin programa
                    record.warehouse_id_domain = [('programa_id', '=', False)]
                else:
                    # Si se selecciona un programa, mostrar almacenes del programa seleccionado
                    record.warehouse_id_domain = [('programa_id', '=', record.programa_id.id)]
            elif self.env.user.has_group('prefectura_inventario.group_stock_program_manager'):
                # Administrador de programa: solo almacenes de su programa
                user_programa = self.env.user.employee_id.programa_id
                record.warehouse_id_domain = [('programa_id', '=', user_programa.id)] if user_programa else [('id', '=', False)]
            else:
                # Usuario regular: no ve almacenes (o ajusta según tus necesidades)
                record.warehouse_id_domain = [('id', '=', False)]

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if 'programa_id' in fields_list:
            user = self.env.user
            employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
            if employee and employee.programa_id:
                defaults['programa_id'] = employee.programa_id.id
        return defaults

    @api.model
    def create(self, vals):
        if 'warehouse_id' in vals and 'programa_id' not in vals:
            warehouse = self.env['stock.warehouse'].browse(vals['warehouse_id'])
            vals['programa_id'] = warehouse.programa_id.id
        return super(StockPickingType, self).create(vals)

    def write(self, vals):
        if 'warehouse_id' in vals:
            warehouse = self.env['stock.warehouse'].browse(vals['warehouse_id'])
            vals['programa_id'] = warehouse.programa_id.id
        return super(StockPickingType, self).write(vals)

    def _search(self, args, offset=0, limit=None, order=None, access_rights_uid=None):
        if self._context.get('filtrar_programa'):
            args = args if args else []
            if self.env.user.programa_id:
                args = [('programa_id', '=', self.env.user.programa_id.id)] + args
            else:
                args = [('id', '=', False)]
        return super()._search(args, offset=offset, limit=limit, order=order, 
                             access_rights_uid=access_rights_uid)