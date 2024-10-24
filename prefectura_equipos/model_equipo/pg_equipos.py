# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo import models, fields, api
import json

class Equipos(models.Model): 
    _name = 'pg_equipos.pg_equipos'
    _description = 'Activo'
    _inherit = [ 'mail.thread', 'mail.activity.mixin']
        
   
    
    name = fields.Char(string='Nombre del Equipo', required=True)
    warranty_start_date = fields.Date('Inicio de Garantía', tracking=True)
    start_date = fields.Date('Fecha de puesta en producción', tracking=True)
    sigla = fields.Char(string='Sigla')  
    programa_id = fields.Many2one(string='Reparto', comodel_name='pf.programas', ondelete='restrict', required=True,
                                 default=lambda s: s.env.company.id) 
    grupo_id = fields.Many2one(string='Grupo', comodel_name='pg_equipos.grupo', required=True, ondelete='restrict', tracking=True, )    
    categoria_id = fields.Many2one(string='Categoria', comodel_name='pg_equipos.categoria', ondelete='restrict', required=True,tracking=True )   
    tipo_id = fields.Many2one(string='Nombre del equipo', comodel_name='pg_equipos.nombre_equipo', ondelete='restrict', required=True,tracking=True )  
    serial = fields.Char('Serial no.', size=64,tracking=True)
    pg_marca_id_domain = fields.Char ( compute = "_compute_pg_marca_id_domain" , readonly = True, store = False, )
    image_medium = fields.Binary("Medium-sized image")
    marca_id = fields.Many2one(string='Marca', comodel_name='pg_equipos.marca', ondelete='restrict',required=True, tracking=True)    
    modelo_id = fields.Many2one(string='Modelo', comodel_name='pg_equipos.modelo', ondelete='restrict',required=True, tracking=True)      
    company_id = fields.Many2one('pf.programas', 'Company', required=True, default=lambda s: s.env.company.id, index=True,)  
    departamento_id = fields.Many2one(string='Departamento', comodel_name='hr.department', ondelete='restrict', 
                                      domain="[('company_id','=',programa_id)]",)
    empleado_id = fields.Many2one('hr.employee', domain="[('company_id','!=',False),('company_id','=',programa_id)]", string='Responsable del Activo', required=True, tracking=True)                                                                                                
    user_id = fields.Many2one('res.users', 'Usuario', related='empleado_id.user_id', readonly=True, store=True,)       
    estado_id = fields.Selection(string='Estado', selection=[('op', 'Operativo'), ('mant', 'Mantenimiento'),('op_lim_men', 'Operativo con limitaciones menores'),
                                                             ('op_lim_may', 'Operativo con limitaciones mayores'), ('no_op', 'No operativo')],tracking=True)
    detalle_caracteristicas_ids = fields.One2many('pg_equipos.det_caracteristica', 'pg_equipos_id', 'Características de activos',) 
    #MODIFICACION DE CAMPOS EXISTENTES       @api.model
    warranty_start_date = fields.Date('Inicio de Garantía', tracking=True)
    purchase_date = fields.Date('Fecha de Adquisiciòn', required=True, tracking=True )
    warranty_end_date = fields.Date('Fin de Garantía', tracking=True)  
    maintenance_date = fields.Datetime(string='Fecha de Mantenimiento', tracking=True)
    tipo_activo = fields.Selection(string='Tipo de activo', selection=[('ordinario', 'Ordinario'), ('estrategico', 'Estratégico')],default='ordinario') 
    
    descripcion = fields.Char(string='Descripcion',)    
    
    file_biblioteca_ids = fields.Many2many('ir.attachment', 'pg_equipos_biblioteca_rel', 'activo_id', 'archivo_id', string="Archivos",
                                    help='Adjuntar los documentos del activo', copy=False)
              
    _sql_constraints = [('name_unique', 'UNIQUE(name)',"Nombre  del activo debe ser único!!"),
                        ('pg_equipos_number_serie', 'UNIQUE(serial)',"Serial ingresado ya existe!!"),
                        ] 
    
    
    @api.constrains('name','serial')
    def _check_pg_equipos_number(self):       
        for record in self:         
          if not(record.serial):
            raise ValidationError("Debe ingresar el serial del Equipo")
         
            
     
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
        self.tipo_id = False    
    
    @api.onchange('tipo_id')
    def _onchange_tipo_id(self):
      for record in self:
        if(record.tipo_id):
          caracteristicas = self.env['pg_equipos.config_caracteristica'].search([('grupo_id','=',record.grupo_id.id)],limit=1).caracteristica_ids   
          caracteristica_obligatorio = caracteristicas.filtered(lambda valor: valor.es_obligatorio == True)  
          record.detalle_caracteristicas_ids = False        
          for linea in caracteristica_obligatorio:          
            self.detalle_caracteristicas_ids = [(0, 0,  { 'caracteristica_id':linea.caracteristica_id})]
            
      
    @api.depends('tipo_id.abreviatura','marca_id.name','modelo_id.name','serial')
    def _concatenar_nombre_activo(self):
      for line in self: 
        _nombre = ""        
        if line.tipo_id:
          _nombre=str(line.tipo_id.abreviatura.upper())                  
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
              
    @api.model
    def create(self, vals):                
      result = super(Equipos, self).create(vals)       
      return result     
    
    def write(self, values):      
      result = super(Equipos, self).write(values)    
      return result
   
    
    def ver_activos(self):
        _condicion = [(id,'=',False)]
        if self.user_has_groups('prefectura_equipos.grupo_equipos_administrador_general') or self.user_has_groups('prefectura_equipos.grupo_equipos_registrador_general'):
          _condicion = [(1,'=',1)]
        elif self.user_has_groups('prefectura_equipos.grupo_equipos_registrador_sucursal'):
          _condicion = [('programa_id','=',self.env.user.company_id.id)]  
        
        diccionario= {
                        'name': ('Ingreso de Activos'),        
                        'domain': _condicion,
                        'res_model': 'pg_equipos.pg_equipos',
                        'views': [(self.env.ref('prefectura_equipos.pg_equiposs_tree_view').id, 'tree'),(self.env.ref('prefectura_equipos.pg_equiposs_form_view').id, 'form')],
                        'search_view_id':[self.env.ref('prefectura_equipos.pg_equiposs_search').id, 'search'],                           
                        'view_mode': 'tree,form',
                        'type': 'ir.actions.act_window',
                        'context': {'search_default_reparto':1},
                    } 
        return diccionario 

    def ver_activos_caracteristicas_especificas(self):        
        _condicion = [(id,'=',False)]
        if self.user_has_groups('prefectura_equipos.grupo_equipos_administrador_general') or self.user_has_groups('prefectura_equipos.group_tecnico_general'):
          _condicion = [(1,'=',1)]
        elif self.user_has_groups('prefectura_equipos.group_tecnico_reparto'):
          grupos = self.env['pg_equipos.permiso_acceso'].search([('programa_id','=',self.env.user.company_id.id)]).grupo_id
          categoria = self.env['pg_equipos.permiso_acceso'].search([('grupo_id','in',grupos.ids)]).categoria_ids
          _condicion = [('programa_id','=',self.env.user.company_id.id),('grupo_id','=',grupos.ids),('categoria_id','=',categoria.ids)]          
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
    
    @api.depends('caracteristica_id')
    def _compute_caracteristica_id_domain(self):
      for record in self:        
        all_caracteristicas= self.env['pg_equipos.config_caracteristica'].search([('tipo_id','=',record.pg_equipos_id.tipo_id.id)],limit=1).caracteristica_ids.caracteristica_id     
        listado_caracteristicas = record.pg_equipos_id.detalle_caracteristicas_ids.caracteristica_id  
        restantes = all_caracteristicas - listado_caracteristicas        
        record.caracteristica_id_domain = json.dumps([('id' , 'in' , restantes.ids)])
        
  

    


    