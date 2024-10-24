from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.osv import expression

class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.onchange('location_id', 'location_dest_id')
    def _check_program_consistency(self):
        for move in self:
            location_programa = move.location_id.get_programa()
            dest_location_programa = move.location_dest_id.get_programa()
            if location_programa and dest_location_programa and location_programa != dest_location_programa:
                raise ValidationError("No se pueden mover productos entre ubicaciones de diferentes programas.")


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    programa_id = fields.Many2one('pf.programas', string='Programa', compute='_compute_programa_id', store=True)
    picking_type_domain = fields.Char(compute='_compute_picking_type_domain', readonly=True, store=False)

    @api.depends('picking_type_id.warehouse_id')
    def _compute_programa_id(self):
        for picking in self:
            picking.programa_id = self.env.programa_id

    @api.onchange('picking_type_id')
    def _onchange_picking_type(self):
        if self.picking_type_id and self.picking_type_id.warehouse_id:
            programa = self.picking_type_id.warehouse_id.lot_stock_id.get_programa()
            if programa:
                self.programa_id = programa
                # Limpiar ubicaciones cuando cambia el tipo de operación
                self.location_id = False
                self.location_dest_id = False

    @api.depends('programa_id')
    def _compute_picking_type_domain(self):
        for record in self:
            if self.env.user.has_group('stock.group_stock_manager'):
                # Administrador ve todos los tipos de operación
                record.picking_type_domain = "[]"  
            else:
                # Usuarios normales solo ven tipos de operación de su programa
                user_programa = self.env.user.employee_id.programa_id
                if user_programa:
                    record.picking_type_domain = f"[('programa_id', '=', {user_programa.id})]"
                else:
                    record.picking_type_domain = "[('id', '=', False)]"
