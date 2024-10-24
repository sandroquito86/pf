from odoo import models, fields, api

class MedicineProduct(models.Model):
    _inherit = 'product.template'

    sale_ok = fields.Boolean(      
        default=False,
        readonly=True
    )

    # Modificamos list_price para que sea readonly con valor predeterminado 0
    list_price = fields.Float(
        'Sales Price', 
        default=0.0,
        digits='Product Price',
        readonly=True
    )

    @api.model
    def create(self, vals):
        # Aseguramos que sale_ok siempre sea False al crear
        vals['sale_ok'] = False
        # Aseguramos que list_price sea 0 si no se proporciona
        vals['list_price'] = vals.get('list_price', 0.0)
        return super(MedicineProduct, self).create(vals)

    def write(self, vals):
        # Aseguramos que sale_ok no pueda ser cambiado a True
        if 'sale_ok' in vals:
            vals['sale_ok'] = False
        # Evitamos que list_price se cambie a un valor diferente de 0
        if 'list_price' in vals:
            vals['list_price'] = 0.0
        return super(MedicineProduct, self).write(vals)

    # es_medicina = fields.Boolean('Es Medicamento', default=True)
    # active_ingredient = fields.Char('Principio Activo')
    # dosage_id = fields.Many2one(
    #     'prefectura_inventario.items', 
    #     string='Dosificación',
    #     domain=lambda self: [('catalogo_id', '=', self.env.ref('prefectura_inventario.catalogo_unidades_medida').id)]
    # )
    # forma_farmaceutica_id = fields.Many2one(
    #     'prefectura_inventario.items', 
    #     string='Forma Farmacéutica',
    #     domain=lambda self: [('catalogo_id', '=', self.env.ref('prefectura_inventario.catalogo_formas_farmaceuticas').id)]
    # )
    # via_administracion_id = fields.Many2one(
    #     'prefectura_inventario.items', 
    #     string='Vía de Administración',
    #     domain=lambda self: [('catalogo_id', '=', self.env.ref('prefectura_inventario.catalogo_via_administracion').id)]
    # )
    # frecuencia_id = fields.Many2one(
    #     'prefectura_inventario.items', 
    #     string='Frecuencia de Administración',
    #     domain=lambda self: [('catalogo_id', '=', self.env.ref('prefectura_inventario.catalogo_frecuencia_administracion').id)]
    # )
    # requires_prescription = fields.Boolean('Requiere Receta')

    # @api.model
    # def create(self, vals):
    #     vals['tracking'] = 'lot'  # Asegura seguimiento por lote
    #     return super(MedicineProduct, self).create(vals)