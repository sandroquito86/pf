from odoo import models, fields, api
from odoo.exceptions import ValidationError

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    programa_id = fields.Many2one('pf.programas', string='Programa Asociado', ondelete='restrict')
    code = fields.Char('Abreviatura', size=10)

    _sql_constraints = [
        ('unique_programa', 'unique(programa_id)', 
         'Ya existe un almacén para este programa. Solo se permite un almacén por programa.')
    ]


    @api.model
    def create(self, vals):
        # Crear el almacén
        warehouse = super(StockWarehouse, self).create(vals)        
        # Si tiene programa_id, actualizar todas las ubicaciones creadas automáticamente
        if warehouse.programa_id:
            # Buscar todas las ubicaciones asociadas al almacén
            locations = self.env['stock.location'].search([('warehouse_id', '=', warehouse.id)])
            # Actualizar el programa_id en todas las ubicaciones
            if locations:
                locations.write({'programa_id': warehouse.programa_id.id})        
        return warehouse

    def write(self, vals):
        # Si se cambia el programa_id, actualizar las ubicaciones
        res = super(StockWarehouse, self).write(vals)
        if 'programa_id' in vals:
            for warehouse in self:
                locations = self.env['stock.location'].search([('warehouse_id', '=', warehouse.id)])
                if locations:
                    locations.write({'programa_id': warehouse.programa_id.id})
        return res
