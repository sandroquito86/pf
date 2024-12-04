from logging.config import valid_ident
import string
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from babel.dates import format_date
# from datetime import datetime,time, datetime
from datetime import datetime
from datetime import date
import time
import json
global NoTieneHorario
from pytz import timezone
from datetime import timedelta



class ConvoyGenerarHorarios(models.Model):
    _inherit = 'mz.genera.planificacion.servicio'

    
    convoy_id = fields.Many2one('mz.convoy', string='Convoy', tracking=True)



    @api.constrains('servicio_id', 'personal_id')
    def _check_detalle_generahorario(self):
        for record in self:           
            asignacion = self.env['mz.asignacion.servicio'].browse(record.servicio_id.id)                        
            if asignacion.convoy_id:
                continue                
            # Si no es de convoy, aplicamos la validación original
            if not (record.turno_disponibles_ids) and not record.es_replanificacion:
                raise UserError("No se puede guardar AGENDA sino genera detalle de Agenda!!")
            
    def _search(self, args, offset=0, limit=None, order=None, access_rights_uid=None):
        """
        Método _search personalizado para filtrar horarios cuando viene el contexto
        """
        args = args or []
        user = self.env.user
        
        if self._context.get('filtrar_convoy'):
            # Verificar grupos
            if user.has_group('manzana_convoy.group_mz_convoy_coordinador'):
                # Para coordinador: ver solo horarios de programas en sus convoyes
                convoyes = self.env['mz.convoy'].search([
                    ('director_coordinador.user_id', '=', user.id)
                ])
                programa_ids = convoyes.mapped('programa_id').ids
                base_args = [('programa_id', 'in', programa_ids)]
                
            elif user.has_group('manzana_convoy.group_mz_convoy_administrador'):
                # Para admin/asistente: ver horarios con modulo_id = 4
                base_args = [('programa_id.modulo_id', '=', 4)]
                
            args = base_args + args
            
        return super(ConvoyGenerarHorarios, self)._search(
            args, 
            offset=offset, 
            limit=limit, 
            order=order, 
            access_rights_uid=access_rights_uid
        )

# Tabla de horarios
class PlanificacionServicio(models.Model):
    _inherit = 'mz.planificacion.servicio'

    numero = fields.Integer(string='Número',)  
    asignacion_id = fields.Many2one('mz.asignacion.servicio', string='Asignación de Servicio', ondelete='restrict')

    @api.depends('fecha', 'horainicio', 'horafin', 'dia')
    def _compute_horario(self):
        # Primero llamamos al método original
        super()._compute_horario()        
        # Luego modificamos solo los registros que necesitamos
        for record in self:           
            if not (record.fecha and record.horainicio and record.horafin):
                record.horario = f"Turno: {record.numero} (Fecha: {record.fecha})"