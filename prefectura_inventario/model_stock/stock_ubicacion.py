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
        if 'programa_id' not in vals and vals.get('location_id'):
            parent_location = self.browse(vals['location_id'])
            parent_programa = parent_location.get_programa()
            if parent_programa:
                vals['programa_id'] = parent_programa.id
        return super(StockLocation, self).create(vals)

    def write(self, vals):
        if 'programa_id' not in vals and vals.get('location_id'):
            parent_location = self.env['stock.location'].browse(vals['location_id'])
            parent_programa = parent_location.get_programa()
            if parent_programa:
                vals['programa_id'] = parent_programa.id
        return super(StockLocation, self).write(vals)

    def filter_locations_by_program(self):
        action = {
            'name': 'Ubicaciones',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.location',
            'view_mode': 'tree,form',
            'context': self.env.context,
        }
        if self.env.user.has_group('stock.group_stock_manager'):
            # Administrador: ve todas las ubicaciones
            return action
        elif self.env.user.has_group('prefectura_inventario.group_stock_program_manager'):
            # Administrador de programa: solo ubicaciones de su programa
            user_programa = self.env.user.employee_id.programa_id            
            if user_programa:
                action['domain'] = [('programa_id', '=', user_programa.id)]          
        else:
            # Usuario regular: no ve ubicaciones (o ajusta según tus necesidades)
            action['domain'] = [('id', '=', False)]
        return action


      