import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.misc import clean_context


class ProductReplenish(models.TransientModel):
    _inherit = 'product.replenish'

    warehouse_id_domain = fields.Char(compute="_compute_warehouse_id_domain", readonly=True, store=False)
    warehouse_id = fields.Many2one('stock.warehouse', string='Almacén', required=True)
    location_id_domain = fields.Char ( compute = "_compute_location_id_domain" , readonly = True, store = False, )
    location_dest_id = fields.Many2one('stock.location', string='Ubicación Destino', domain=[('usage', '=', 'internal')], required=True)


    
    @api.onchange('warehouse_id')
    def _onchange_warehouse_id(self):
        self.location_dest_id = False

    @api.depends('product_id')
    def _compute_warehouse_id_domain(self):
        for record in self:
            if self.env.user.has_group('stock.group_stock_manager'):
                # Administrador: ve todos los almacenes
                record.warehouse_id_domain = "[]"
            elif self.env.user.has_group('prefectura_inventario.group_stock_program_manager'):
                # Administrador de programa: solo almacenes de su programa
                user_programa = self.env.user.employee_id.programa_id
                if user_programa:
                    record.warehouse_id_domain = f"[('programa_id', '=', {user_programa.id})]"
                else:
                    record.warehouse_id_domain = "[('id', '=', False)]"
            else:
                # Usuario regular: no ve almacenes
                record.warehouse_id_domain = "[('id', '=', False)]"


    @api.depends('warehouse_id')
    def _compute_location_id_domain(self):
        for record in self:
            if self.env.user.has_group('stock.group_stock_manager') or \
               self.env.user.has_group('prefectura_inventario.group_stock_program_manager'):
                if record.warehouse_id:
                    # Si se selecciona un almacén, mostrar sus ubicaciones internas
                    record.location_id_domain = f"[('warehouse_id', '=', {record.warehouse_id.id}), ('usage', '=', 'internal')]"
                else:
                    # Si no se selecciona almacén, mostrar todas las ubicaciones internas
                    record.location_id_domain = "[('usage', '=', 'internal')]"
            else:
                # Usuario regular: no ve ubicaciones
                record.location_id_domain = "[('id', '=', False)]"

    @api.model
    def default_get(self, fields):
        res = super(ProductReplenish, self).default_get(fields)
        
        if 'warehouse_id' in fields:
            # Obtener el almacén por defecto
            default_warehouse = self.env['stock.warehouse'].search([('programa_id', '=', False)], limit=1)
            
            if default_warehouse:
                res['warehouse_id'] = default_warehouse.id
            
            # Si el usuario es administrador de programa, buscar el almacén de su programa
            if self.env.user.has_group('prefectura_inventario.group_stock_program_manager'):
                user_programa = self.env.user.employee_id.programa_id
                if user_programa:
                    program_warehouse = self.env['stock.warehouse'].search([('programa_id', '=', user_programa.id)], limit=1)
                    if program_warehouse:
                        res['warehouse_id'] = program_warehouse.id

        return res

    def _prepare_run_values(self):
        values = super(ProductReplenish, self)._prepare_run_values()
        if self.location_dest_id:
            values['location_id'] = self.location_dest_id.id
        return values

    def _create_purchase_order(self, values):
        po = super(ProductReplenish, self)._create_purchase_order(values)
        if po and self.location_dest_id:
            for line in po.order_line:
                line.orderpoint_id.location_id = self.location_dest_id.id
        return po

    @api.model
    def _get_warehouse_domain(self):
        if self.env.user.has_group('stock.group_stock_manager'):
            return []  # Sin restricciones para administradores
        elif self.env.user.has_group('your_module.group_stock_program_manager'):
            user_programa = self.env.user.employee_id.programa_id
            if user_programa:
                return [('programa_id', '=', user_programa.id)]
        return [('id', '=', False)]  # No mostrar almacenes si no tiene permisos


    def launch_replenishment(self):        
        uom_reference = self.product_id.uom_id
        self.quantity = self.product_uom_id._compute_quantity(self.quantity, uom_reference, rounding_method='HALF-UP')
        try:
            now = self.env.cr.now()
            self.env['procurement.group'].with_context(clean_context(self.env.context)).run([
                self.env['procurement.group'].Procurement(
                    self.product_id,
                    self.quantity,
                    uom_reference,
                    self.warehouse_id.lot_stock_id,  # Location
                    _("Reabastecimiento Manual"),  # Name
                    _("Reabastecimiento Manual"),  # Origin
                    self.warehouse_id.company_id,
                    self._prepare_run_values()  # Values
                )
            ])
            move = self._get_record_to_notify(now)
            notification = self._get_replenishment_order_notification(move)
            act_window_close = {
                'type': 'ir.actions.act_window_close',
                'infos': {'done': True},
            }
            if notification:
                notification['params']['next'] = act_window_close
                return notification
            return act_window_close
        except UserError as error:
            raise UserError(error)