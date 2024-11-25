# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime
from datetime import date
from datetime import timedelta
from babel.dates import format_date
from datetime import datetime, timedelta

class AgendarServicio(models.Model):
    _inherit = 'mz.agendar_servicio'
    
    

    convoy_id = fields.Many2one('mz.convoy', string='Convoy', required=True, tracking=True)
    convoy_id_domain = fields.Char(compute="_compute_programa_convoy_id_domain", readonly=True, store=False, )
    beneficiario_convoy_id_domain = fields.Char(compute="_compute_beneficiario_convoy_id_domain", readonly=True, store=False, )
    dependiente_convoy_id_domain = fields.Char(compute="_compute_dependiente_convoy_id_domain", readonly=True, store=False, )
    dependiente_convoy_id_domain = fields.Char(compute="_compute_dependiente_convoy_id_domain", readonly=True, store=False, )
    personal_convoy_id_domain = fields.Char(compute="_compute_personal_convoy_id_domain", readonly=True, store=False, )

    @api.constrains('convoy_id', 'beneficiario_id', 'servicio_id')
    def _check_duplicate_beneficiario_servicio(self):
        for record in self:
            if record.convoy_id and record.beneficiario_id and record.servicio_id:
                # Buscamos si existe otro registro con el mismo convoy, beneficiario y servicio
                duplicate = self.search([
                    ('id', '!=', record.id),  # Excluimos el registro actual
                    ('convoy_id', '=', record.convoy_id.id),
                    ('beneficiario_id', '=', record.beneficiario_id.id),
                    ('servicio_id', '=', record.servicio_id.id),
                    ('state', 'not in', ['cancelado', 'finalizado'])  # Opcional: excluir estados finalizados/cancelados
                ])

                if duplicate:
                    raise UserError(
                        f'El beneficiario {record.beneficiario_id.name} ya tiene agendado el '
                        f'servicio {record.servicio_id.name}'
                    )


    @api.onchange('fecha_solicitud')
    def _onchange_fecha_solicitud(self):
        for record in self:
            if record.convoy_id:
                fecha_solicitud = record.fecha_solicitud
                if fecha_solicitud:
                    if not (record.convoy_id.fecha_inicio_evento <= fecha_solicitud <= record.convoy_id.fecha_hasta_evento):
                        raise UserError('La fecha seleccionada debe estar dentro del rango de fechas del convoy: {} - {}'.format(
                            record.convoy_id.fecha_inicio_evento.strftime('%d/%m/%Y'),
                            record.convoy_id.fecha_hasta_evento.strftime('%d/%m/%Y')
                        ))
            else:
                super(AgendarServicio, self)._onchange_fecha_solicitud()
        

    @api.model
    def create(self, vals):
        if vals.get('convoy_id'):
            # Buscar la cabecera existente usando el convoy_id
            generar_horario = self.env['mz.genera.planificacion.servicio'].search([
                ('servicio_id', '=', vals.get('servicio_id')),
                ('personal_id', '=', vals.get('personal_id')),
                ('convoy_id', '=', vals.get('convoy_id')),
                ('active', '=', True),
            ], limit=1)
            
            if not generar_horario:
                raise UserError('No existe una planificación activa para este servicio y personal en el convoy seleccionado')
                
            fecha_actual = fields.Date.today()
            
            # Obtener el último número usado para esta cabecera en la misma fecha
            ultimo_horario = self.env['mz.planificacion.servicio'].search([
                ('generar_horario_id', '=', generar_horario.id),
                ('fecha', '=', fecha_actual)
            ], order='numero desc', limit=1)
            
            # Determinar el siguiente número
            siguiente_numero = (ultimo_horario.numero + 1) if ultimo_horario else 1
            
            # Crear el horario usando la cabecera existente
            horario_vals = {
                'generar_horario_id': generar_horario.id,
                'fecha': fecha_actual,
                'estado': 'activo',
                'creado_por_usuario_id': self.env.user.id,
                'turno_extra': 'no',
                'maximo_beneficiarios': generar_horario.maximo_beneficiarios,
                'numero': siguiente_numero,
                'beneficiario_ids': [(6, 0, [vals.get('beneficiario_id')])] if vals.get('beneficiario_id') else [(6, 0, [])]
            }
            
            horario = self.env['mz.planificacion.servicio'].create(horario_vals)
            
            # Asignar el horario creado al registro de agendar_servicio
            vals['horario_id'] = horario.id
            vals['fecha_solicitud'] = fecha_actual
            vals['state'] = 'solicitud'
            
            return super(AgendarServicio, self).create(vals)
    
    @api.onchange('personal_id')
    def _onchange_personal_id(self):
        for record in self:
            if not record.convoy_id:
                record.fecha_solicitud = False
                record.horario_id = False
                if record.servicio_id and record.personal_id:
                    domain = [
                        ('generar_horario_id.servicio_id', '=', record.servicio_id.id),
                        ('generar_horario_id.personal_id', '=', record.personal_id.id),
                        ('fecha', '>=', fields.Date.today()),
                        ('estado', '=', 'activo'),
                    ]
                    horarios_planificados = self.env['mz.planificacion.servicio'].search(domain)
                    
                    horarios_disponibles = horarios_planificados.filtered(
                        lambda h: h.beneficiarios_count < h.maximo_beneficiarios
                    )
                    if not horarios_disponibles:
                        raise UserError(f"No hay Turnos disponibles para el servicio de {record.servicio_id.servicio_id.name} con {record.personal_id.name}.")
            else:              
                fecha_actual = datetime.now() - timedelta(hours=5)
                record.fecha_solicitud = fecha_actual.date()
 
  
    @api.depends('convoy_id')
    def _compute_beneficiario_convoy_id_domain(self):
        for record in self:
            if record.convoy_id:
                beneficiario_ids = record.convoy_id.beneficiario_ids.mapped('beneficiario_id').ids
                record.beneficiario_convoy_id_domain = [('id', 'in', beneficiario_ids)]
            else:
                record.beneficiario_convoy_id_domain = [('id', 'in', [])]

    @api.depends('beneficiario_id', 'tipo_beneficiario')
    def _compute_dependiente_convoy_id_domain(self):
        for record in self:
            if record.tipo_beneficiario == 'dependiente' and record.beneficiario_id:
                # Filtrar dependientes del beneficiario seleccionado
                record.dependiente_convoy_id_domain = [('beneficiario_id', '=', record.beneficiario_id.id)]
            else:
                # Si no es dependiente o no hay beneficiario seleccionado, dominio vacío
                record.dependiente_convoy_id_domain = [('id', 'in', [])]

    @api.depends('convoy_id')
    def _compute_programa_convoy_id_domain(self):
        for record in self:
            convoy_ids =[]           
            user = self.env.user
            domain = [('state', '=', 'ejecutando')]                
            if user.has_group('manzana_convoy.group_mz_convoy_coordinador'):
                domain.append(('director_coordinador.user_id', '=', user.id))
            elif user.has_group('manzana_convoy.group_mz_convoy_operador'):
                domain.append(('operadores_ids.user_id', 'in', [user.id]))                
            convoy_ids = record.convoy_id.search(domain).ids
            record.convoy_id_domain = [('id', 'in', convoy_ids)]

    @api.depends('servicio_id')
    def _compute_personal_convoy_id_domain(self):
        for record in self:
            if record.servicio_id:
                record.personal_convoy_id_domain = [('id', 'in', record.servicio_id.personal_ids.ids)]
            else:
                record.personal_convoy_id_domain = [('id', 'in', [])]
            
    
    @api.onchange('convoy_id')
    def _onchange_field(self):
        for record in self:
            if(record.convoy_id):
                record.programa_id = record.convoy_id.programa_id
    
    