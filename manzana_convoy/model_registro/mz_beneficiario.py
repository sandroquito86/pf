from odoo import models, fields, api
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta



class Beneficiario(models.Model):
    _inherit = 'mz.beneficiario'
    _description = 'Catálogo de Beneficiarios'


    tipo_registro = fields.Selection([('masivo', 'Registro Masivo'), ('asistencia', 'Registro por Asistencia'), ('socioeconomico', 'Registro Socioeconómico')], string='Tipo de Registro', 
                                     required=True, default='masivo')
    num_documento = fields.Char('Número de Documento', required=True)
    nombres = fields.Char('Nombres', required=True)
    apellidos = fields.Char('Apellidos', required=True)
    es_extranjero = fields.Boolean('¿Es Migrante Extranjero?')    
    celular = fields.Char('Celular')
    operadora_id = fields.Many2one('pf.items', string='Operadora', domain=lambda self: [('catalogo_id', '=', self.env.ref('manzana_convoy.catalogo_operadoras').id)])
    # Campos de asistencia
    fecha_nacimiento = fields.Date('Fecha de Nacimiento')   
    estado_civil_id = fields.Many2one('pf.items', string='Estado Civil', domain=lambda self: [('catalogo_id', '=', self.env.ref('manzana_convoy.catalogo_estado_civil').id)])
    genero_id = fields.Many2one('pf.items', string='Género', domain=lambda self: [('catalogo_id', '=', self.env.ref('manzana_convoy.catalogo_genero').id)])
    canton = fields.Char('Cantón')
    parroquia = fields.Char('Parroquia')
    direccion = fields.Char('Dirección de domicilio')
   

    _sql_constraints = [('num_documento_uniq', 'UNIQUE(num_documento)', 'Ya existe un beneficiario con este número de documento.')]

    @api.onchange('tiene_discapacidad_hogar')
    def _onchange_tiene_discapacidad_hogar(self):
        if self.tiene_discapacidad_hogar == 'no':
            self.tipo_discapacidad_hogar_id = False
        elif self.tiene_discapacidad_hogar == 'si' and not self.tipo_discapacidad_hogar_id:
            # Buscar el registro "NINGUNA" por defecto
            ninguna = self.env['pf.items'].search([
                ('catalogo_id', '=', self.env.ref('manzana_convoy.catalogo_convoy_tipo_discapacidad').id),
                ('name', '=', 'NINGUNA')
            ], limit=1)
            if ninguna:
                self.tipo_discapacidad_hogar_id = ninguna.id 

    @api.onchange('mujeres_embarazadas', 'mujeres_embarazadas_chequeos', 'mujeres_embarazadas_menores')
    def _onchange_field(self):
        for record in self:            
            if record.mujeres_embarazadas_chequeos > record.mujeres_embarazadas:
                raise UserError('El número de mujeres embarazadas que asisten a chequeos no puede ser mayor al número total de mujeres embarazadas.')            
            if record.mujeres_embarazadas_menores > record.mujeres_embarazadas:
                raise UserError('El número de mujeres embarazadas menores de 18 años no puede ser mayor al número total de mujeres embarazadas.')

    def action_view_masivo(self):
        self.ensure_one()
        action = {
            'name': 'Beneficiarios Registro Masivo',
            'type': 'ir.actions.act_window',
            'res_model': 'mz.beneficiario',
            'view_mode': 'tree,form',
            'domain': [('tipo_registro', '=', 'masivo')],
            'context': {'default_tipo_registro': 'masivo'},
            'target': 'current',
        }
        return action

    def action_view_asistencia(self):
        self.ensure_one()
        action = {
            'name': 'Beneficiarios Registro por Asistencia',
            'type': 'ir.actions.act_window',
            'res_model': 'mz.beneficiario',
            'view_mode': 'tree,form',
            'domain': [('tipo_registro', '=', 'asistencia')],
            'context': {'default_tipo_registro': 'asistencia'},
            'target': 'current',
        }
        return action

    def action_view_socioeconomico(self):
        self.ensure_one()
        action = {
            'name': 'Beneficiarios Registro Socioeconómico',
            'type': 'ir.actions.act_window',
            'res_model': 'mz.beneficiario',
            'view_mode': 'tree,form',
            'domain': [('tipo_registro', '=', 'socioeconomico')],
            'context': {'default_tipo_registro': 'socioeconomico'},
            'target': 'current',
        }
        return action

   
