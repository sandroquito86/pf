from odoo import models, fields, api

class ProductTamplate(models.Model):
    _inherit = 'product.template'

    sale_ok = fields.Boolean(default=False, readonly=True, string='Se puede vender')

    # Modificamos list_price para que sea readonly con valor predeterminado 0
    list_price = fields.Float(default=0.0, digits='Product Price', readonly=True)



    def action_view_stock_moves(self):
        action = self.env.ref('stock.stock_move_action').read()[0]
        action['domain'] = [('product_id.product_tmpl_id', 'in', self.ids)]
        action['context'] = {'search_default_groupby_location_id': 1}
        return action

    def action_view_stock_move_lines(self):
        action = self.env.ref('stock.stock_move_line_action').read()[0]
        action['domain'] = [('product_id.product_tmpl_id', 'in', self.ids)]
        action['context'] = {'search_default_groupby_location_id': 1}
        return action

    @api.model
    def create(self, vals):
        # Aseguramos que sale_ok siempre sea False al crear
        vals['sale_ok'] = False
        # Aseguramos que list_price sea 0 si no se proporciona
        vals['list_price'] = vals.get('list_price', 0.0)
        vals['type'] = 'product'
        vals['detailed_type'] = 'product'
        return super(ProductTamplate, self).create(vals)

    def write(self, vals):
        # Aseguramos que sale_ok no pueda ser cambiado a True
        if 'sale_ok' in vals:
            vals['sale_ok'] = False
        # Evitamos que list_price se cambie a un valor diferente de 0
        if 'list_price' in vals:
            vals['list_price'] = 0.0
        if 'type' in vals or 'detailed_type' in vals:
            vals['type'] = 'product'
            vals['detailed_type'] = 'product'
        return super(ProductTamplate, self).write(vals)

   