from odoo import models, fields, api
from odoo.exceptions import ValidationError

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    programa_id = fields.Many2one('pf.programas', string='Programa Asociado', ondelete='restrict')
    code = fields.Char('Abreviatura', size=10)

    domain_programa_general_id = fields.Char(string='Domain Programa',compute='_compute_domain_general_programas')

    @api.depends('code')
    def _compute_domain_general_programas(self):
        for record in self:
            # user = self.env.user
            # es_coordinador = user.has_group('manzana_de_cuidados.group_coordinador_manzana')
            # es_sistema = user.has_group('manzana_de_cuidados.group_beneficiario_manager')

            # if es_coordinador:
            #     # Si es coordinador, solo ve su programa
            #     if user.programa_id:
            #         record.domain_programa_general_id = [('id', '=', user.programa_id.id)]
            #     else:
            #         record.domain_programa_general_id = [('id', '=', False)]
            # elif es_sistema:
            #     # Si es sistema, ve todos los programas del módulo 2
            #     programas = self.env['pf.programas'].search([
            #         ('modulo_id', '=', self.env.ref('prefectura_base.modulo_2').id)
            #     ])
            #     record.domain_programa_general_id = [('id', 'in', programas.ids)] if programas else [('id', '=', False)]
            # else:
            #     # Para otros usuarios, no ven ningún programa
            record.domain_programa_general_id = [('id', '=', False)]

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
