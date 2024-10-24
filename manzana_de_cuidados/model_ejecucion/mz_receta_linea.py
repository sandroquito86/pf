from odoo import models, fields, api


class RecetaLinea(models.Model):
    _name = 'mz.receta.linea'
    _description = 'Línea de Receta Médica'

    consulta_id = fields.Many2one('mz.consulta', string='Consulta', required=True, ondelete='cascade')
    producto_id = fields.Many2one('product.product', string='Producto', required=True)
    cantidad = fields.Float(string='Cantidad', required=True, default=1.0)
    instrucciones = fields.Text(string='Instrucciones de uso')
    en_inventario = fields.Boolean(string='En Inventario', compute='_compute_en_inventario', store=True)

    @api.depends('producto_id', 'cantidad')
    def _compute_en_inventario(self):
        for linea in self:
            linea.en_inventario = linea.producto_id.qty_available >= linea.cantidad

    @api.onchange('producto_id', 'cantidad')
    def _onchange_producto_cantidad(self):
        if self.producto_id and self.cantidad:
            self.en_inventario = self.producto_id.qty_available >= self.cantidad