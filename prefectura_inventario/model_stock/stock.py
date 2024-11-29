from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.osv import expression

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    employee_id = fields.Many2one(string='Responsble', comodel_name='hr.employee', ondelete='restrict',
                                default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1), required=True)

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id and self.employee_id.user_id.partner_id:
            self.partner_id = self.employee_id.user_id.partner_id.id

    @api.onchange('picking_type_id')
    def _onchange_picking_type_id(self):
        if self.picking_type_id:
            if self.picking_type_id.code == 'incoming':
                self.location_id = self.picking_type_id.default_location_src_id.id or self.env.ref('stock.stock_location_suppliers').id
                self.location_dest_id = self.picking_type_id.default_location_dest_id.id if self.picking_type_id.default_location_dest_id else self.env['stock.location'].search([('usage', '=', 'internal')], limit=1).id
            elif self.picking_type_id.code == 'outgoing':
                self.location_id = self.picking_type_id.default_location_src_id.id 
                self.location_dest_id = self.picking_type_id.default_location_dest_id.id or self.env.ref('stock.stock_location_customers').id
            else:
                self.location_id = self.picking_type_id.default_location_src_id.id
                self.location_dest_id = self.picking_type_id.default_location_dest_id.id
