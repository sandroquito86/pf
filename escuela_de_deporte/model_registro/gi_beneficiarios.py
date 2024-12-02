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
    

    

    
  