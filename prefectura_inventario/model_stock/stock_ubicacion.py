from odoo import models, fields, api
from odoo.exceptions import ValidationError


class StockLocation(models.Model):
    _inherit = 'stock.location'

    programa_id = fields.Many2one('pf.programas', string='Programa Asociado')
    adm = fields.Boolean(string='Administrador', compute='_compute_administrador')
    location_id_domain = fields.Char ( compute = "_compute_location_id_domain" , readonly = True, store = False, )
    location_id = fields.Many2one(
        'stock.location', 'Parent Location', index=True, ondelete='cascade', check_company=True,
        help="The parent location that includes this location. Example : The 'Dispatch Zone' is the 'Gate 1' parent location.")
  


    @api.depends('programa_id')
    def _compute_location_id_domain(self):
        for record in self:
            if self.env.user.has_group('stock.group_stock_manager'):
                if not record.programa_id:
                    # Si no se selecciona programa, mostrar ubicaciones de almacenes sin programa
                    warehouses_without_program = self.env['stock.warehouse'].search([('programa_id', '=', False)])
                    record.location_id_domain = [('warehouse_id', 'in', warehouses_without_program.ids)]                    
                else:
                    # Si se selecciona un programa, mostrar ubicaciones del programa seleccionado
                    warehouses_of_program = self.env['stock.warehouse'].search([('programa_id', '=', record.programa_id.id)])
                    record.location_id_domain = [('warehouse_id', 'in', warehouses_of_program.ids)] 
            elif self.env.user.has_group('prefectura_inventario.group_stock_program_manager'):
                # Administrador de programa: solo ubicaciones de su programa
                warehouses_of_program = self.env['stock.warehouse'].search([('programa_id', '=', record.programa_id.id)])
                record.location_id_domain = [('warehouse_id', 'in', warehouses_of_program.ids)]           
            else:
                # Usuario regular: no ve ubicaciones (o ajusta según tus necesidades)
                record.location_id_domain = [('id', '=',False)]



    @api.depends('programa_id')
    def _compute_administrador(self):
        for record in self:
            record.adm = self.env.user.has_group('stock.group_stock_manager')

    @api.onchange('programa_id')
    def onchange_programa_id(self):
        if self.programa_id:
            parent_location = self.env['stock.location'].search([
                ('company_id', '=', self.env.company.id),
                ('location_id', '=', False)  # Ubicación de nivel superior
            ], limit=1)
            if parent_location:
                self.location_id = parent_location.id

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if 'programa_id' in fields_list:
            user = self.env.user
            employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
            if employee and employee.programa_id:
                defaults['programa_id'] = employee.programa_id.id
        return defaults

    # obtener el programa asociado a una ubicación.
    def get_programa(self):
        self.ensure_one()
        return self.programa_id
   
    
    @api.model
    def create(self, vals):
        # Si se está creando una ubicación vista y tiene un warehouse_id
        if vals.get('usage') == 'view' and vals.get('warehouse_id'):
            warehouse = self.env['stock.warehouse'].browse(vals['warehouse_id'])
            if warehouse.programa_id:
                vals['programa_id'] = warehouse.programa_id.id
        return super(StockLocation, self).create(vals)

    def write(self, vals):
        if 'programa_id' not in vals and vals.get('location_id'):
            parent_location = self.env['stock.location'].browse(vals['location_id'])
            parent_programa = parent_location.get_programa()
            if parent_programa:
                vals['programa_id'] = parent_programa.id
        return super(StockLocation, self).write(vals)

    def _search(self, args, offset=0, limit=None, order=None, access_rights_uid=None):
        if self._context.get('filtrar_programa'):
            # Aseguramos que args sea una lista antes de modificarla
            args = args if args else []
            # Agregamos el dominio para filtrar por programa
            if self.env.user.programa_id:
                args = [('programa_id', '=', self.env.programa_id.id)] + args
            else:
                # Si el usuario no tiene programa asignado, no mostramos ningún almacén
                args = [('id', '=', False)]  # Dominio que no retornará resultados
        
        return super()._search(args, offset=offset, limit=limit, order=order, access_rights_uid=access_rights_uid)

      