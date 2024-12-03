from odoo import models, fields, api
from odoo.exceptions import ValidationError

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    programa_id = fields.Many2one('pf.programas', string='Programa Asociado', ondelete='restrict')
    code = fields.Char('Abreviatura', size=10)
    domain_programa_id = fields.Char(string='Domain Programa',compute='_compute_domain_programas')

    _sql_constraints = [
        ('unique_programa', 'unique(programa_id)', 
         'Ya existe un almacén para este programa. Solo se permite un almacén por programa.')
    ]

    @api.constrains('programa_id')
    def _check_almacen_sin_programa(self):
        for record in self:
            # Buscar todos los almacenes sin programa asignado
            almacenes_sin_programa = self.search([('programa_id', '=', False), ('id', '!=', record.id)])            
            # Si el registro actual no tiene programa y ya existe otro almacén sin programa
            if not record.programa_id and almacenes_sin_programa:
                raise ValidationError('Solo se permite tener un almacén en la Prefectura del Guayas.')

    @api.depends('code')
    def _compute_domain_programas(self):
        for record in self:
            user = self.env.user
            es_coordinador = user.has_group('manzana_de_cuidados.group_coordinador_manzana')
            es_sistema = user.has_group('manzana_de_cuidados.group_beneficiario_manager')
            es_stock_manager = user.has_group('stock.group_stock_manager')
            if es_stock_manager:
                # Si es stock manager, puede ver todos los programas
                programas = self.env['pf.programas'].search([])
                record.domain_programa_id = [('id', 'in', programas.ids)] if programas else [('id', '=', False)]
            elif es_coordinador:
                # Si es coordinador, solo ve su programa
                if user.programa_id:
                    record.domain_programa_id = [('id', '=', user.programa_id.id)]
                else:
                    record.domain_programa_id = [('id', '=', False)]
            elif es_sistema:
                # Si es sistema, ve todos los programas del módulo 2
                programas = self.env['pf.programas'].search([('modulo_id', '=', self.env.ref('prefectura_base.modulo_2').id)])
                record.domain_programa_id = [('id', 'in', programas.ids)] if programas else [('id', '=', False)]
            else:
                # Para otros usuarios, no ven ningún programa
                record.domain_programa_id = [('id', '=', False)]

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
    
   

    @api.depends('code')
    def _compute_domain_programas(self):
        for record in self:
            user = self.env.user
            es_coordinador = user.has_group('manzana_de_cuidados.group_coordinador_manzana')
            es_sistema = user.has_group('manzana_de_cuidados.group_beneficiario_manager')

            if es_coordinador:
                # Si es coordinador, solo ve su programa
                if user.programa_id:
                    record.domain_programa_id = [('id', '=', user.programa_id.id)]
                else:
                    record.domain_programa_id = [('id', '=', False)]
            elif es_sistema:
                # Si es sistema, ve todos los programas del módulo 2
                programas = self.env['pf.programas'].search([('modulo_id', '=', self.env.ref('prefectura_base.modulo_2').id)])
                record.domain_programa_id = [('id', 'in', programas.ids)] if programas else [('id', '=', False)]
            else:
                # Para otros usuarios, no ven ningún programa
                record.domain_programa_id = [('id', '=', False)]

        
    def _search(self, args, offset=0, limit=None, order=None, access_rights_uid=None):
        if self._context.get('filtrar_programa_almacen'):
            args = args if args else []
            user = self.env.user
            
            es_coordinador = user.has_group('manzana_de_cuidados.group_coordinador_manzana')
            es_sistema = user.has_group('manzana_de_cuidados.group_beneficiario_manager')
            es_stock_manager = user.has_group('stock.group_stock_manager')
            
            # Verificar contexto de manzana
            es_contexto_manzana = self._context.get('manzana_context', False)

            if es_stock_manager and not es_contexto_manzana:
                # Solo ve todos los almacenes si NO está en contexto manzana
                pass
            elif es_coordinador:
                if es_contexto_manzana:
                    # Coordinador en manzana solo ve su programa
                    programa_id = user.programa_id.id if user.programa_id else False
                    if programa_id:
                        args = [('programa_id', '=', programa_id)] + args
                    else:
                        args = [('id', '=', False)]  # No muestra nada si no tiene programa
            elif es_sistema:
                if es_contexto_manzana:
                    # Sistema en manzana solo ve módulo 2
                    modulo_2 = self.env.ref('prefectura_base.modulo_2').id
                    args = [('programa_id.modulo_id', '=', modulo_2)] + args
                else:
                    args = [('id', '=', False)]
            else:
                # Otros usuarios no ven ningún almacén
                args = [('id', '=', False)]

        return super()._search(args, offset=offset, limit=limit, order=order, access_rights_uid=access_rights_uid)
            