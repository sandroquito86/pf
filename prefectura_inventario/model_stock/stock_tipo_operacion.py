from odoo import models, fields, api

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'
    
    programa_id = fields.Many2one('pf.programas', string='Programa Asociado', related='warehouse_id.programa_id', store=True)


    def _search(self, args, offset=0, limit=None, order=None, access_rights_uid=None):
        if self._context.get('filtrar_programa_tipo_operacion'):
            args = args if args else []
            user = self.env.user
            es_coordinador = user.has_group('manzana_de_cuidados.group_coordinador_manzana')
            es_sistema = user.has_group('manzana_de_cuidados.group_beneficiario_manager')
            es_stock_manager = user.has_group('stock.group_stock_manager')
            
            # Verificar contexto de manzana
            es_contexto_manzana = self._context.get('manzana_context', False)

            if es_stock_manager and not es_contexto_manzana:
                # Ve todos los tipos de operación
                pass
            elif es_coordinador:
                if es_contexto_manzana:
                    programa_id = user.programa_id.id if user.programa_id else False
                    if programa_id:
                        # Usar SQL directo para evitar recursión
                        self.env.cr.execute("""
                            SELECT spt.id 
                            FROM stock_picking_type spt
                            JOIN stock_warehouse sw ON spt.warehouse_id = sw.id
                            JOIN pf_programas pp ON sw.programa_id = pp.id
                            WHERE pp.id = %s
                        """, (programa_id,))
                        
                        tipo_operacion_ids = [r[0] for r in self.env.cr.fetchall()]
                        if tipo_operacion_ids:
                            args = [('id', 'in', tipo_operacion_ids)] + args
                        else:
                            args = [('id', '=', False)]
                    else:
                        args = [('id', '=', False)]
            elif es_sistema:
                if es_contexto_manzana:
                    modulo_2 = self.env.ref('prefectura_base.modulo_2').id
                    self.env.cr.execute("""
                        SELECT spt.id 
                        FROM stock_picking_type spt
                        JOIN stock_warehouse sw ON spt.warehouse_id = sw.id
                        JOIN pf_programas pp ON sw.programa_id = pp.id
                        WHERE pp.modulo_id = %s
                    """, (modulo_2,))
                    
                    tipo_operacion_ids = [r[0] for r in self.env.cr.fetchall()]
                    if tipo_operacion_ids:
                        args = [('id', 'in', tipo_operacion_ids)] + args
                    else:
                        args = [('id', '=', False)]
                else:
                    args = [('id', '=', False)]
            else:
                args = [('id', '=', False)]

        return super()._search(args, offset=offset, limit=limit, order=order, access_rights_uid=access_rights_uid)