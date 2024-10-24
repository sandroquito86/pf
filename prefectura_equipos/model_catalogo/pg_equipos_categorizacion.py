from odoo.exceptions import ValidationError
from odoo import models, fields, api
from string import ascii_letters, digits, whitespace


class Grupo(models.Model):
    _name = 'pg_equipos.grupo'
    _description = 'Grupos de Equipos'
    _inherit = [ 'mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string="Grupo", help='Escriba el nombre del Grupo', required=True,tracking=True)   
    categoria_ids = fields.One2many(string='Categorías', comodel_name='pg_equipos.categoria', inverse_name='grupo_id')  
    active = fields.Boolean(string='Activo/Inactivo', default='True' )
      
    _sql_constraints = [('grupo_unico', 'unique(name)','Ya existe un grupo con este nombre')]
    
    @api.constrains('name')
    def _check_name_modelo_insensitive(self):
        for record in self:
            model_ids = record.search([('id', '!=',record.id)])        
            list_names = [x.name.upper() for x in model_ids if x.name]        
            if record.name.upper() in list_names:
                raise ValidationError("Ya existe el grupo: %s , no se permiten valores duplicados !!" % (record.name.upper()))  
 

class Categoria(models.Model):
    _name = 'pg_equipos.categoria'
    _inherit = [ 'mail.thread', 'mail.activity.mixin']
    _description = 'Categoría'  
    _rec_name = 'name' 
   
    name = fields.Char('Categoría', required=True, tracking=True) 
    complete_name = fields.Char('Nombre completo', compute='_compute_complete_name', store=True)  
    descripcion = fields.Text('Descripción', tracking=True)       
    abreviatura = fields.Char(string="Abreviatura", required=True,tracking=True)      
    marca_ids = fields.Many2many(string='Marcas', comodel_name='pg_equipos.marca', relation='categoria_marca_rel', 
                                      column1='categoria_id', column2='marca_id', tracking=True, domain="[('active','=',True)]")  
    grupo_id = fields.Many2one(string='Grupo', comodel_name='pg_equipos.grupo', required=True, ondelete='restrict', tracking=True)  
    tipo_ids = fields.One2many(string='Tipos', comodel_name='pg_equipos.nombre_equipo', inverse_name='categoria_id',)  
     
    active = fields.Boolean(string='Activo/Inactivo', default='True' )


    @api.depends('name', 'grupo_id.name')
    def _compute_complete_name(self):
        for record in self:
            if record.name:
                record.complete_name = ' %s / %s'  % (record.grupo_id.name,record.name)

    def name_get(self):
        result = []
        for category in self:                     
            if self._context.get('complete_name'):      
                name = category.complete_name
            else:
                name = category.name
            result.append((category.id, name))    
        return result 
    
    
         
    def _track_subtype(self, init_values):        
        self.ensure_one() #garantiza la uitransferencia de un solo registro       
        return self.env.ref('prefectura_equipos.asset_historico_categoria')               
        return sModelosuper(Categoria, self)._track_subtype(init_values)
       
    _sql_constraints = [('name_unique', 'UNIQUE(grupo_id,name)',"Nombre de la categoria debe ser unico dentro de un mismo grupo!!"),
                        ('abreviatura_unique', 'UNIQUE(grupo_id,abreviatura)',"Nombre de la abreviatura debe ser unico dentro de un mismo grupo!!")] 
    
    @api.constrains('name')
    def _check_name_categoria_insensitive(self):
        for record in self:
            model_ids = record.search([('id', '!=',record.id),('grupo_id', '=',record.grupo_id.id)])        
            list_names = [x.name.upper() for x in model_ids if x.name]        
            if record.name.upper() in list_names:
                raise ValidationError("Ya existe una categoría con el nombre: %s dentro de este grupo" % (record.name.upper()))
            abreviatura_names = [x.abreviatura.upper() for x in model_ids if x.abreviatura]        
            if record.abreviatura.upper() in abreviatura_names:
                raise ValidationError("Ya existe la abreviatura: %s en este grupo" % (record.abreviatura.upper()))
   
    @api.model
    def create(self, values):   
        values['abreviatura'] =  values['abreviatura'].upper()
        result = super(Categoria, self).create(values)    
        return result
    
    def write(self, values):
        if values.get('abreviatura'):
           values['abreviatura'] =  values['abreviatura'].upper()
        result = super(Categoria, self).write(values)    
        return result
    


class NombreEquipo(models.Model):
    _name = 'pg_equipos.nombre_equipo'
    _description = 'Tipo de Activo'
    _inherit = [ 'mail.thread', 'mail.activity.mixin']

    abreviatura = fields.Char(string="Abreviatura", required=True, tracking=True)    
    name = fields.Char(string="Nombre del Equipo", required=True, tracking=True)    
    categoria_id = fields.Many2one(string='Categoria de Activo', comodel_name='pg_equipos.categoria', ondelete='restrict', required=True, tracking=True )    
    componente_ids = fields.Many2many(string='Componentes', comodel_name='asset.catalogo_componente', relation='tipo_catalogo_componente_rel', column1='tipo_id', column2='componente_id',
                                      domain="[('categoria_id','=',categoria_id)]")
    
    active = fields.Boolean(string='Activo/Inactivo', default='True' )
    
    _sql_constraints = [('abreviatura_unique', 'UNIQUE(categoria_id,abreviatura)', "Abreviatura ingresada ya existe en esta categoría!!"),
                        ('name_unique', 'UNIQUE(categoria_id,name)', "Tipo de activo ingresado ya existe en esta categoría!!")]    
    
    @api.constrains('name','categoria_id')
    def _check_name_marca_insensitive(self):
        for record in self:
            model_ids = record.search([('id', '!=',record.id),('categoria_id', '=',record.categoria_id.id)])        
            list_names = [x.name.upper() for x in model_ids if x.name]        
            if record.name.upper() in list_names:
                raise ValidationError("Ya existe : %s , no se permiten valores duplicados dentro de la misma categoria" % (record.name.upper()))   
            list_abreviatura = [x.abreviatura.upper() for x in model_ids if x.abreviatura]        
            if record.abreviatura.upper() in list_abreviatura:
                raise ValidationError("Ya existe : %s , no se permiten abreviaturas duplicadas dentro de la misma categoria" % (record.abreviatura.upper()))
      
           
    @api.onchange('categoria_id')
    def _onchange_categoria_id(self):
        self.componente_ids = False
        
    
    def asignar_componentes(self):
        _condicion = [(id,'=',False)]
        if self.user_has_groups('prefectura_equipos.grupo_equipos_administrador_general') or self.user_has_groups('prefectura_equipos.group_tecnico_general'):
            _condicion = [(1,'=',1)]            
        elif self.user_has_groups('prefectura_equipos.group_tecnico_reparto'):
            grupos = self.env['asset.permiso_acceso'].search([('programa_id','=',self.env.user.company_id.id)]).grupo_id
            categoria = self.env['asset.permiso_acceso'].search([('grupo_id','in',grupos.ids)]).categoria_ids
            _condicion = [('categoria_id','in',categoria.ids)]        
        diccionario= {
                        'name': ('Asignación de componentes'),        
                        'domain': _condicion,
                        'res_model': 'pg_equipos.nombre_equipo',
                        'views': [(self.env.ref('prefectura_equipos.view_tipo_activo_tecnico_tree').id, 'tree'),(self.env.ref('prefectura_equipos.view_tipo_activo_tecnico_form').id, 'form')],
                        'search_view_id':[self.env.ref('prefectura_equipos.view_tipo_activo_tecnico_search').id, 'search'],                           
                        'view_mode': 'tree,form',
                        'type': 'ir.actions.act_window',                       
                        'context': {'search_default_grupo':1,'search_default_categoria':1}
                    } 
        return diccionario