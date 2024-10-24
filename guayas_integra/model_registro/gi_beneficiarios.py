from odoo import models, fields, api
from random import randint
from datetime import date
from dateutil.relativedelta import relativedelta


class giBeneficiarios(models.Model):
    _name = 'gi.beneficiario'
    _inherits = {'pf.beneficiario': 'beneficiario_id'} 
    _description = 'Beneficiarios Guayas Integra'   

    
    beneficiario_id = fields.Many2one(
        string='field_name',
        comodel_name='pf.beneficiario',
        ondelete='restrict',
    )
    

    
    # name = fields.Char(string="Nombre del Beneficiario", compute="_compute_name", store=True)
    # image = fields.Image(string="Imagen del Beneficio")  # Campo para la imagen
    # category_ids = fields.Many2many('pf.categoria_beneficario', 'gi_beneficiario_categoria_rel', 'beneficiario_id', 'categoria_id', 
    #                                 string='Categorías')  
    # apellido_paterno = fields.Char(string='Apellido Paterno')
    # apellido_materno = fields.Char(string='Apellido Materno')
    # primer_nombre = fields.Char(string='Primer Nombre')
    # segundo_nombre = fields.Char(string='Segundo Nombre')   
    # fecha_nacimiento = fields.Date(string="Fecha de Nacimiento") 
    # edad = fields.Char(string="Edad", compute="_compute_edad", store=True)
    # cedula = fields.Char(string='Cédula de Identidad') 
    # pais_id = fields.Many2one('res.country', string='Pais', ondelete='restrict')
    # provincia_id = fields.Many2one("res.country.state", string='Provincia', ondelete='restrict', 
    #                                domain="[('country_id', '=?', pais_id)]")
    # user_id = fields.Many2one('res.users', string="Usuario", help="Usuario asociado para acceder al sistema")
    # modulo_ids = fields.Many2many('pf.modulo',  string="Módulos", help="Selecciona los módulos a los que pertenece este beneficiario")
    
  