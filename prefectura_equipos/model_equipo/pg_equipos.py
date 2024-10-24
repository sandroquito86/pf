# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo import models, fields, api
import json

class Equipos(models.Model): 
    _name = 'pg_equipos.pg_equipos'
    _description = 'Activo'
    _inherit = [ 'mail.thread', 'mail.activity.mixin']
        
   
    
    name = fields.Char(string='Nombre del Equipo', compute='_compute_name', store=True, tracking=True)
    grupo_id = fields.Many2one(string='Grupo', comodel_name='pg_equipos.grupo', required=True, ondelete='restrict', tracking=True, )    
    categoria_id = fields.Many2one(string='Categoria', comodel_name='pg_equipos.categoria', ondelete='restrict', required=True,tracking=True )   
    nombre_equipo = fields.Many2one(string='Nombre del equipo', comodel_name='pg_equipos.nombre_equipo', ondelete='restrict', required=True,tracking=True )  
    serial = fields.Char('Serial no.', size=64,tracking=True, required=True)
    inicio_garantia = fields.Date('Inicio de Garantía', tracking=True)
    start_date = fields.Date('Fecha de puesta en producción', tracking=True)
    programa_id = fields.Many2one(string='Programa', comodel_name='pf.programas', ondelete='restrict', required=True,
                                 default=lambda s: s.env.programa_id) 
    empleado_id = fields.Many2one('hr.employee', domain="[('programa_id','!=',False),('programa_id','=',programa_id)]", string='Responsable del Equipo', tracking=True)    
    user_id = fields.Many2one('res.users', 'Usuario', related='empleado_id.user_id', readonly=True, store=True,)     
    pg_marca_id_domain = fields.Char ( compute = "_compute_pg_marca_id_domain" , readonly = True, store = False, )
    image = fields.Binary("Image", attachment=True)
    image_medium = fields.Binary("Medium-sized image", attachment=True)
    image_small = fields.Binary("Small-sized image", attachment=True)
    marca_id = fields.Many2one(string='Marca', comodel_name='pg_equipos.marca', ondelete='restrict',required=True, tracking=True)    
    modelo_id = fields.Many2one(string='Modelo', comodel_name='pg_equipos.modelo', ondelete='restrict',required=True, tracking=True) 
    estado_id = fields.Selection(string='Estado', selection=[('op', 'Operativo'), ('mant', 'Mantenimiento'),('op_lim_men', 'Operativo con limitaciones menores'),
                                                             ('op_lim_may', 'Operativo con limitaciones mayores'), ('no_op', 'No operativo')],tracking=True, required=True)
    detalle_caracteristicas_ids = fields.One2many('pg_equipos.det_caracteristica', 'pg_equipos_id', 'Características de activos',) 
    fecha_adquisicion = fields.Date('Fecha de Adquisiciòn', required=True, tracking=True )
    fin_garantia = fields.Date('Fin de Garantía', tracking=True)  
    
              
    _sql_constraints = [('name_unique', 'UNIQUE(name)',"Nombre  del activo debe ser único!!"),
                        ('pg_equipos_number_serie', 'UNIQUE(serial)',"Serial ingresado ya existe!!"),] 

    def _search(self, args, offset=0, limit=None, order=None, access_rights_uid=None):
        if self._context.get('filtrar_programa') and self.env.user.programa_id:
            args = [('programa_id', '=', self.env.user.programa_id.id)] + (args or [])            
        return super(Equipos, self)._search(args, offset=offset, limit=limit, order=order, access_rights_uid=access_rights_uid)
        
    @api.depends('nombre_equipo', 'marca_id', 'modelo_id', 'serial')
    def _compute_name(self):
        for record in self:
            # Inicializar partes del nombre
            partes_nombre = []            
            # Agregar tipo si existe
            if record.nombre_equipo:
                partes_nombre.append(record.nombre_equipo.name)            
            # Agregar marca si existe
            if record.marca_id:
                partes_nombre.append(record.marca_id.name)            
            # Agregar modelo si existe
            if record.modelo_id:
                partes_nombre.append(record.modelo_id.name)            
            # Agregar serial si existe
            if record.serial:
                partes_nombre.append(f"[{record.serial}]")            
            # Unir todas las partes con espacios
            record.name = " - ".join(filter(None, partes_nombre))            
            # Si no hay ningún dato, poner un valor por defecto
            if not record.name:
                record.name = "Nuevo Equipo"  

    @api.constrains('detalle_caracteristicas_ids')
    def _check_caracteristica_obligatorio(self):
      for record in self:          
        caracteristicas = self.env['pg_equipos.config_caracteristica'].search([('grupo_id','=',record.grupo_id.id)],limit=1).caracteristica_ids  
        caracteristica_obligatorio = caracteristicas.filtered(lambda valor: valor.es_obligatorio == True ).caracteristica_id                   
        caracteristicas_ingresadas = record.detalle_caracteristicas_ids.caracteristica_id        
        diferencia =  caracteristica_obligatorio - caracteristicas_ingresadas                
        if(diferencia):
          raise ValidationError("Las siguientes caracteristicas  son obligatorias:\n{}".format(diferencia.mapped('name')))
        else:
          for lineas in record.detalle_caracteristicas_ids:
            if not (lineas.valor_id):
              raise ValidationError("Existen caracteristicas definidas que no tienen un valor..")
            
    @api.onchange('grupo_id')
    def _onchange_grupo_id(self):
      self.categoria_id = False
      
      
        
    @api.depends('categoria_id.marca_ids')
    def _compute_pg_marca_id_domain(self):
      for record in self:       
        if(record.categoria_id):   
          record.pg_marca_id_domain = [('id', 'in', record.categoria_id.marca_ids.ids)]           
        else:
          record.pg_marca_id_domain = [('id', '=', False)]
          
    @api.onchange('categoria_id')
    def _onchange_categoria_id(self):
      for record in self:
        self.nombre_equipo = False    
    
    @api.onchange('nombre_equipo')
    def _onchange_nombre_equipo(self):
      for record in self:
        if(record.nombre_equipo):
          caracteristicas = self.env['pg_equipos.config_caracteristica'].search([('grupo_id','=',record.grupo_id.id)],limit=1).caracteristica_ids   
          caracteristica_obligatorio = caracteristicas.filtered(lambda valor: valor.es_obligatorio == True)  
          record.detalle_caracteristicas_ids = False        
          for linea in caracteristica_obligatorio:          
            self.detalle_caracteristicas_ids = [(0, 0,  { 'caracteristica_id':linea.caracteristica_id})]
            
      
    @api.depends('nombre_equipo','marca_id.name','modelo_id.name','serial')
    def _concatenar_nombre_activo(self):
      for line in self: 
        _nombre = ""        
        if line.nombre_equipo:
          _nombre=str(line.nombre_equipo.upper())                  
        if line.marca_id:          
          _nombre += "-" + str(line.marca_id.name.upper())
        if line.modelo_id:          
          _nombre += "-" + str(line.modelo_id.name.upper())       
        if line.serial:          
          _nombre += "-" +str(line.serial.upper())
        line.name = _nombre
            
              
    @api.onchange('marca_id')    
    def _onchange_field(self):        
      self.modelo_id = False       
      
     
    @api.onchange('programa_id')
    def _onchange_programa_id(self):
        self.empleado_id = False
              
    @api.model_create_multi
    def create(self, vals_list):
        # Asegurar que vals_list sea una lista
        if not isinstance(vals_list, list):
            vals_list = [vals_list]
        
        for vals in vals_list:
            # Si se proporciona una imagen, procesar los diferentes tamaños
            if vals.get('image'):
                image = vals['image']
                vals['image_medium'] = image
                vals['image_small'] = image

        return super(Equipos, self).create(vals_list)

    def write(self, vals):
        # Si se actualiza la imagen, actualizar todos los tamaños
        if vals.get('image'):
            image = vals['image']
            vals['image_medium'] = image
            vals['image_small'] = image

        return super(Equipos, self).write(vals)
   
    
 
    def ver_activos_caracteristicas_especificas(self):        
        _condicion = [(id,'=',False)]
        if self.user_has_groups('prefectura_equipos.grupo_equipos_administrador_general') or self.user_has_groups('prefectura_equipos.group_tecnico_general'):
          _condicion = [(1,'=',1)]
        elif self.user_has_groups('prefectura_equipos.group_tecnico_reparto'):
          grupos = self.env['pg_equipos.permiso_acceso'].search([('programa_id','=',self.env.user.programa_id.id)]).grupo_id
          categoria = self.env['pg_equipos.permiso_acceso'].search([('grupo_id','in',grupos.ids)]).categoria_ids
          _condicion = [('programa_id','=',self.env.user.programa_id.id),('grupo_id','=',grupos.ids),('categoria_id','=',categoria.ids)]          
        diccionario= {
                        'name': ('Características Específicas y Componentes'),        
                        'domain': _condicion,
                        'res_model': 'pg_equipos.pg_equipos',
                        'views': [(self.env.ref('prefectura_equipos.pg_equiposs_caracteristicas_especificas_tree_view').id, 'tree'),(self.env.ref('prefectura_equipos.pg_equiposs__pg_equiposs_caracteristicas_especificas_form_view').id, 'form')],
                        'search_view_id':[self.env.ref('prefectura_equipos.pg_equiposs_caracteristicas_especificas_search').id, 'search'],                           
                        'view_mode': 'tree,form',
                        'type': 'ir.actions.act_window',
                        'context': {'search_default_reparto':1},
                    } 
        return diccionario 
      
      
class DetalleCaracteristicaEquipo(models.Model):
    _name = "pg_equipos.det_caracteristica"
    _description = 'Detalle Caracteristica' 
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'caracteristica_id'
    
    pg_equipos_id = fields.Many2one('pg_equipos.pg_equipos', string="Activos", ondelete='restrict', required=True, index=True, )  
    caracteristica_id_domain = fields.Char ( compute = "_compute_caracteristica_id_domain" , readonly = True, store = False, )
    caracteristica_id = fields.Many2one('pg_equipos.catalogo_caracteristica', string="Característica", required=True, ondelete='restrict', tracking=True)       
    valor_id = fields.Many2one('pg_equipos.caracteristica_valor', string="Valor Característica",  ondelete='restrict', tracking=True,
                               domain="[('caracteristica_id', '=', caracteristica_id)]")  
    display_name = fields.Char(
        string='Característica y Valor',
        compute='_compute_display_name',
        store=True
    )

    @api.depends('caracteristica_id', 'valor_id')
    def _compute_display_name(self):
        for record in self:
            if record.caracteristica_id and record.valor_id:
                record.display_name = f"{record.caracteristica_id.name}: {record.valor_id.name}"
            else:
                record.display_name = ''
    
    @api.depends('caracteristica_id', 'pg_equipos_id.grupo_id')
    def _compute_caracteristica_id_domain(self):
        for record in self:
            if record.pg_equipos_id and record.pg_equipos_id.grupo_id:
                # Buscar la configuración de características para este grupo
                config_caracteristica = self.env['pg_equipos.config_caracteristica'].search([
                    ('grupo_id', '=', record.pg_equipos_id.grupo_id.id)
                ], limit=1)
                
                if config_caracteristica:
                    # Obtener las características configuradas y ya asignadas
                    all_caracteristicas = config_caracteristica.caracteristica_ids.caracteristica_id
                    caracteristicas_asignadas = record.pg_equipos_id.detalle_caracteristicas_ids.caracteristica_id
                    # Calcular características disponibles
                    disponibles = all_caracteristicas - caracteristicas_asignadas
                    record.caracteristica_id_domain = [('id', 'in', disponibles.ids)]
                else:
                    record.caracteristica_id_domain = [('id', '=', False)]
            else:
                record.caracteristica_id_domain = [('id', '=', False)]