# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError,UserError
from string import ascii_letters, digits
import string




class Area(models.Model):
    _name = 'gi.area'
    _description = 'Areas' 

    
    name = fields.Char(string='Nombre', required=True)
   
    company_domain_id = fields.Char(default="[('phone', '=', '098')]",compute='_compute_author_domain_field')
    attachment_ids = fields.Many2many(comodel_name='ir.attachment', relation='hr_doc_solicitud_movimiento_documento_rel', 
                                      column1='rechazo_solicitud_id', column2='attachment_id', string='Archivo Adjunto')  
    
    reparto_id = fields.Many2one(
        string='Reparto',
        comodel_name='res.company',
        ondelete='restrict',
    )

    
    @api.onchange('name')
    def _onchange_field(self):
        pass
        # raise UserError("Este es un mensaje de error personalizado para el usuario.")
        
    @api.depends('name')
    def _compute_author_domain_field(self):
        for record in self:
            record.company_domain_id = "[('id', '=', 1)]"
    
    
    

    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', "El área debe ser único.")
    ]    

    @api.constrains('name')
    def _check_name_marca_insensitive(self):
        for record in self:
            model_ids = record.search([('id', '!=',record.id)])        
            list_names = [x.name.upper() for x in model_ids if x.name]        
            if record.name.upper() in list_names:
                raise ValidationError("Ya existe el Área: %s , no se permiten valores duplicados" % (record.name.upper())) 
    