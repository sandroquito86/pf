from odoo import api, fields, models, _
from odoo.exceptions import UserError
import re

class Colaborador(models.Model):
    _inherit = 'hr.employee'
   

    # Datos personales   
    latitud = fields.Float(string='Latitud', digits=(16, 8))
    longitud = fields.Float(string='Longitud', digits=(16, 8))    
    # Información profesional
    cargo = fields.Char(string='Cargo', required=True, tracking=True)
    experiencia = fields.Text(string='Experiencia', required=True)   

    @api.constrains('identificacion')
    def _check_identificacion(self):
        for record in self:
            if record.identificacion:
                cedula = re.sub(r'[\s-]', '', record.identificacion)
                if not cedula.isdigit():
                    raise UserError(_('La cédula debe contener solo números'))
                if len(cedula) != 10:
                    raise UserError(_('La cédula debe tener 10 dígitos'))
   

    @api.constrains('latitud', 'longitud')
    def _check_coordenadas(self):
        for record in self:
            if record.latitud and (record.latitud < -90 or record.latitud > 90):
                raise UserError(_('La latitud debe estar entre -90 y 90 grados'))
            if record.longitud and (record.longitud < -180 or record.longitud > 180):
                raise UserError(_('La longitud debe estar entre -180 y 180 grados'))