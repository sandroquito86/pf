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

    @api.depends('picking_type_id.warehouse_id')
    def _compute_programa_id(self):
        for picking in self:
            if picking.picking_type_id and picking.picking_type_id.warehouse_id:
                picking.programa_id = picking.picking_type_id.warehouse_id.lot_stock_id.get_programa()
            else:
                picking.programa_id = False

    @api.onchange('picking_type_id')
    def _onchange_picking_type(self):
        if self.picking_type_id and self.picking_type_id.warehouse_id:
            self.programa_id = self.picking_type_id.warehouse_id.lot_stock_id.get_programa()