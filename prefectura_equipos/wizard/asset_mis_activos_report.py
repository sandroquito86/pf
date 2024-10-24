from odoo import models, fields, api
from odoo.exceptions import ValidationError

class MisActivosWizard(models.TransientModel):   
    _name = 'asset_wizard.mis_activos'
    _description = 'Mis activos'
    
    
    
    tipo_reporte = fields.Selection(string='Tipo de reporte', selection=[('todo', 'Todos mis activos'), ('criterio', 'Criterio de busqueda')], required=True)
    
    grupo_ids = fields.Many2many(string='Grupos',   comodel_name='pg_equipos.grupo', relation='asset_mis_activos_grupo_wizard_rel', column1='mis_activos', column2='grupo_id',)
    categoria_ids = fields.Many2many(string='Categorias',   comodel_name='pg_equipos.categoria', relation='asset_mis_activos_categoria_wizard_rel', column1='mis_activos', column2='categoria_id',)
    tipo_ids = fields.Many2many(string='Tipo',   comodel_name='pg_equipos.nombre_equipo', relation='asset_mis_activos_categoria_tipo_wizard_rel', column1='mis_activos', column2='tipo_id',)
    
    
    
    
#     categoria_ids = fields.Many2many(string='Categorias', comodel_name='pg_equipos.categoria', relation='asset_wizard_caracteristicas_categoria_rel',
#                                      column1='caracteristica_id',column2='categoria_id',)
#     caracteristica_ids = fields.Many2many(string='Caracteristica', comodel_name='product.attribute', relation='asset_wizard_caracteristicas_atribute_rel',
#                                      column1='caracteristica_id',column2='atributo_id',)
#     valor_ids = fields.Many2many(string='Valor', comodel_name='product.attribute.value', relation='asset_wizard_caracteristicas_atribute_valor_rel',
#                                      column1='caracteristica_id',column2='atributo_valor_id',)    
#     asset_ids = fields.Many2many(string='Activos', comodel_name='asset.asset', relation='asset_caracteristicas_activo_rel', 
#                                  column1='caracteristicas_id', column2='activo_id', )

#     @api.onchange('categoria_ids')
#     def _onchange_categorias_id(self):  
#         diccionario={ 'caracteristica_ids':[]}                     
#         if(self.categoria_ids):
#             categoria = self.env['asset.config.categoria'].search([('categoria_id','in',self.categoria_ids.ids)])  
#             atributo_ids = categoria.caracteristicas_ids.atributo_id.ids                
#             diccionario['caracteristica_ids'] = [('id', 'in', atributo_ids)]      
#             if(self.caracteristica_ids):
#                 for record in self.caracteristica_ids.ids:
#                     if(record not in atributo_ids):
#                         self.caracteristica_ids = [(2,record)]       
#         else:
#             self.caracteristica_ids = [(5,0,0)]
#         return {'domain': diccionario} 
        
#     @api.onchange('caracteristica_ids')
#     def _onchange_caracteristicas_id(self):  
#         diccionario={ 'valor_ids':[]}          
#         if(self.caracteristica_ids):  
#             valores =  self.caracteristica_ids.value_ids.ids          
#             diccionario['valor_ids'] = [('id', 'in',valores )] 
#             if(self.valor_ids):
#                 for record in self.valor_ids.ids:
#                     if(record not in valores):
#                         self.valor_ids = [(2,record)]   
#         return {'domain': diccionario} 

#     @api.onchange('valor_ids')
#     def _onchange_valor_ids(self):
#         if(self.valor_ids):
#             activos=self.env['asset.detalle.caracteristica'].search([('valor_id','in',self.valor_ids.ids)]).asset_id
#             self.asset_ids = activos
#             # raise ValidationError("llego {}".format(activos))

    def print_report(self):
        docs=[]
        # for record in self.asset_ids:
        #     docs.append({'id': record.id, 'name': record.name})
        id= 1
        data={
            'form':self.read()[0],
            'ids':1, 
            'forma':{
                'estado':'activo'
            }           
        }       
        return self.env.ref('prefectura_equipos.report_asset_mis_activos').report_action(self, data=data)

    
class ReportMisActivos(models.AbstractModel):
    _name = 'report.asset.mis_activos'
    _description = 'Reporte de mis activos'    

    @api.model
    def _get_report_values(self, docids, data=None):
        ids=data['ids']    
        res =[]   
        activos = self.env['asset.asset'].browse(ids)
        for activo in activos:
            res.append({                
                'name':activo.name,
                'programa_id':activo.programa_id.name,
                'empleado_id':activo.empleado_id.name,
                'asset_number':activo.asset_number,                             
            })
        return {            
            'docs': res,            
        }