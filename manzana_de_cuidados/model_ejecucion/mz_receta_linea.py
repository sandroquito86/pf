from odoo import models, fields, api
from odoo.exceptions import UserError



class RecetaLinea(models.Model):
    _name = 'mz.receta.linea'
    _description = 'Línea de Receta Médica'

    consulta_id = fields.Many2one('mz.consulta', string='Consulta', required=True, ondelete='cascade')
    producto_id = fields.Many2one('product.product', string='Producto', required=True)
    domain_producto_id = fields.Char(string='Domain Producto', compute='_compute_domain_producto_id')
    cantidad = fields.Float(string='Cantidad', required=True, default=1.0)
    instrucciones = fields.Text(string='Instrucciones de uso')
    en_inventario = fields.Boolean(string='En Inventario', compute='_compute_en_inventario', store=True)

    @api.depends('producto_id', 'cantidad')
    def _compute_en_inventario(self):
        for linea in self:
            if not linea.producto_id or not linea.cantidad:
                linea.en_inventario = False
                continue                
            usuario = self.env.user
            if not usuario.programa_id:
                linea.en_inventario = False
                continue                
            # Buscar ubicaciones del programa
            ubicaciones = self.env['stock.location'].search([('programa_id', '=', usuario.programa_id.id)])  
            # raise UserError(ubicaciones)       
            if not ubicaciones:
                linea.en_inventario = False
                continue                
            # Obtener la cantidad total disponible en todas las ubicaciones del programa
            cantidad_disponible = sum(self.env['stock.quant'].search([
                    ('product_id', '=', linea.producto_id.id), ('location_id', 'in', ubicaciones.ids), ('quantity', '>', 0)]).mapped('quantity'))            
            linea.en_inventario = cantidad_disponible >= linea.cantidad

    @api.depends('consulta_id')
    def _compute_domain_producto_id(self):
        for linea in self:
            if linea.consulta_id:
                linea.domain_producto_id = [('id', '>', 0)]
                # linea.domain_producto_id = [('id', 'in', linea.consulta_id.productos_ids.ids)]
            else:
                linea.domain_producto_id = [('id', 'in', [])]