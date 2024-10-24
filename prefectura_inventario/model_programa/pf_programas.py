from odoo import models, fields, api
from odoo.exceptions import UserError

class PfProgramas(models.Model):
    _inherit = 'pf.programas'

    warehouse_ids = fields.One2many('stock.warehouse', 'programa_id', string='Almacenes')

    def get_warehouses(self):
        return self.env['stock.warehouse'].search([('programa_id', '=', self.id)])

    @api.model
    def create(self, vals):
        programa = super(PfProgramas, self).create(vals)
        programa._create_inventory_structure()
        return programa

    def _create_inventory_structure(self):
        self.ensure_one()
        WarehouseObj = self.env['stock.warehouse']
        
        # Crear almacén con nombre descriptivo
        warehouse_name = f"{self.name} (ALMACÉN)"
        warehouse_vals = {
            'name': warehouse_name,
            'code': self.sigla[:5],
            'company_id': self.sucursal_id.company_id.id,
            'programa_id': self.id,
        }
        warehouse = WarehouseObj.create(warehouse_vals)
        
        # Obtener la ubicación vista (parent location) del almacén
        view_location = self.env['stock.location'].search([
            ('warehouse_id', '=', warehouse.id),
            ('usage', '=', 'view'),
            ('location_id', '=', False)  # Ubicación padre de nivel superior
        ], limit=1)
        
        if view_location:
            view_location.write({
                'programa_id': self.id,
                'name': warehouse_name
            })
        
        # Actualizar la ubicación de existencias
        stock_location = warehouse.lot_stock_id
        stock_location.write({
            'name': 'Existencias',
            'programa_id': self.id,
        })
        
        # Actualizar todas las demás ubicaciones relacionadas
        location_ids = self.env['stock.location'].search([
            ('warehouse_id', '=', warehouse.id)
        ])
        location_ids.write({
            'programa_id': self.id,
        })
        
        # Actualizar nombres completos
        location_ids._compute_complete_name()
        
        return True

    def write(self, vals):
        res = super(PfProgramas, self).write(vals)
        if 'name' in vals or 'sigla' in vals:
            for programa in self:
                warehouses = programa.warehouse_ids
                if warehouses:
                    warehouse_vals = {}
                    if 'name' in vals:
                        warehouse_vals['name'] = f"{programa.name} (ALMACÉN)"
                    if 'sigla' in vals:
                        warehouse_vals['code'] = programa.sigla[:10]
                    if warehouse_vals:
                        warehouses.write(warehouse_vals)
                    if 'name' in vals:
                        locations = self.env['stock.location'].search([('programa_id', '=', programa.id)])
                        locations.write({'name': programa.name})
                        locations._compute_complete_name()
        return res

    def unlink(self):
        for programa in self:
            if programa.warehouse_ids:
                raise UserError("No se puede eliminar un programa con almacenes asociados. Por favor, elimine primero los almacenes.")
        return super(PfProgramas, self).unlink()