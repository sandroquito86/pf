from odoo import models, fields, api
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    def _get_default_location_dest(self):
        return self.env.ref('stock.stock_location_customers').id
    
    domain_location_id = fields.Char(string='Domain Location Source', compute='_compute_domain_location')
    domain_location_dest_id = fields.Char(string='Domain Location Dest', compute='_compute_domain_location_dest')
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


    @api.depends('picking_type_id')
    def _compute_domain_location(self):
        for record in self:
            user = self.env.user
            es_coordinador = user.has_group('manzana_de_cuidados.group_coordinador_manzana')
            es_sistema = user.has_group('manzana_de_cuidados.group_beneficiario_manager')
            es_stock_manager = user.has_group('stock.group_stock_manager')
            es_stock_user = user.has_group('stock.group_stock_user')

            if es_stock_manager or es_stock_user:
                # Stock manager ve todas las ubicaciones físicas
                physical_loc = self.env.ref('stock.stock_location_locations')
                # Obtener ubicaciones físicas excluyendo virtuales y partners
                domain = [
                    '|',
                    ('location_id', '=', physical_loc.id),  # Ubicaciones hijas directas
                    ('location_id.location_id', '=', physical_loc.id)  # Ubicaciones nietas
                ]
                record.domain_location_id = str(domain)
            elif es_coordinador:
                if user.programa_id:
                    # Solo ubicaciones de su programa
                    record.domain_location_id = str([('programa_id', '=', self.env.user.programa_id.id)])
                else:
                    record.domain_location_id = str([('id', '=', False)])
            elif es_sistema:
                # Todas las ubicaciones de programas del módulo 2
                programas = self.env['pf.programas'].search([
                    ('modulo_id', '=', self.env.ref('prefectura_base.modulo_2').id)
                ])
                if programas:
                    record.domain_location_id = str([('programa_id', 'in', programas.ids)])
                else:
                    record.domain_location_id = str([('id', '=', False)])
            else:
                record.domain_location_id = str([('id', '=', False)])

    @api.depends('picking_type_id')
    def _compute_domain_location_dest(self):
        for record in self:
            user = self.env.user
            es_coordinador = user.has_group('manzana_de_cuidados.group_coordinador_manzana')
            es_sistema = user.has_group('manzana_de_cuidados.group_beneficiario_manager')
            # Buscar programas del módulo 2
            programas = self.env['pf.programas'].search([('modulo_id', '=', self.env.ref('prefectura_base.modulo_2').id)])

            if es_coordinador or es_sistema:
                if programas:
                    # Tanto coordinador como sistema pueden enviar a cualquier ubicación de programas del módulo 2
                    record.domain_location_dest_id = str([('programa_id', 'in', programas.ids)])
                else:
                    record.domain_location_dest_id = str([('id', '=', False)])
            else:
                record.domain_location_dest_id = str([('id', '=', False)])

    
    def _search(self, args, offset=0, limit=None, order=None, access_rights_uid=None):
        args = args or []
        user = self.env.user
        es_coordinador = user.has_group('manzana_de_cuidados.group_coordinador_manzana')
        es_sistema = user.has_group('manzana_de_cuidados.group_beneficiario_manager')
        es_stock_manager = user.has_group('stock.group_stock_manager')
        
        # Verificar contexto de manzana
        es_contexto_manzana = self._context.get('manzana_context', False)
        if es_contexto_manzana:         
            picking_type_code = self._context.get('default_picking_type_code')
            domain = []
            
            if es_coordinador and user.programa_id:
                if picking_type_code == 'incoming':
                    # Solo recibidos que van a ubicaciones de mi almacén
                    domain = [
                        ('location_dest_id.programa_id', '=', user.programa_id.id)
                    ]
                elif picking_type_code == 'outgoing':
                    # Solo entregas asociadas a mi programa
                    domain = [
                        ('location_id.programa_id', '=', user.programa_id.id)
                    ]
                elif picking_type_code == 'internal':
                    # Movimientos internos donde origen o destino es de mi almacén
                    domain = ['|',
                        ('location_id.programa_id', '=', user.programa_id.id),
                        ('location_dest_id.programa_id', '=', user.programa_id.id)
                    ]            
            elif es_sistema:
                programas = self.env['pf.programas'].search([
                    ('modulo_id', '=', self.env.ref('prefectura_base.modulo_2').id)
                ])
                if programas:
                    if picking_type_code == 'incoming':
                        domain = [
                            ('location_dest_id.programa_id', 'in', programas.ids)
                        ]
                    elif picking_type_code == 'outgoing':
                        domain = [
                            ('location_id.programa_id', 'in', programas.ids)
                        ]
                    elif picking_type_code == 'internal':
                        domain = ['|',
                            ('location_id.programa_id', 'in', programas.ids),
                            ('location_dest_id.programa_id', 'in', programas.ids)
                        ]
                    
            if domain:
                args = domain + args

        return super()._search(args, offset=offset, limit=limit, order=order, access_rights_uid=access_rights_uid)