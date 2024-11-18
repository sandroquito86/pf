from odoo import models, fields, api
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError


class FichaEvento(models.Model):
    _name = 'mz.convoy'
    _description = 'Ficha de Evento'
    _inherits = {'pf.programas': 'programa_id'} 
    _inherit = ['mail.thread', 'mail.activity.mixin'] 

    # Corrección del campo programa_id para apuntar al modelo correcto
    programa_id = fields.Many2one('pf.programas', string='Programa', ondelete='restrict',  required=True, auto_join=True)
    institucion_anfitriona = fields.Char(string='Institución Anfitriona') 
    director_coordinador = fields.Many2one(string='Coordinador Responsable', comodel_name='hr.employee', ondelete='restrict')       
    # El resto de los campos permanecen igual
    fecha_evento = fields.Date(string='Fecha del Evento')
    dia_semana = fields.Char(string='Día', compute='_compute_dia_semana', store=True)
    lugar = fields.Char(string='Lugar')
    hora_inicio = fields.Float(string='Hora Inicio')
    hora_fin = fields.Float(string='Hora Fin')
    duracion = fields.Char(string='Duración', compute='_compute_duracion', store=True)    
    tipo_evento = fields.Many2one('mz.items', string='Tipo Evento', domain=lambda self: [('catalogo_id', '=', self.env.ref('manzana_convoy.catalogo_tipo_evento').id)])
    formato_evento = fields.Char(string='Formato de Evento')
    numero_asistentes = fields.Integer(string='Número de Asistentes')
    codigo_vestimenta = fields.Char(string='Código de Vestimenta')   
    participacion_prefecta = fields.Many2one('mz.items', string='Participación  Prefecta', domain=lambda self: [('catalogo_id', '=', self.env.ref('manzana_convoy.catalogo_participacion_especifica').id)])
    tiempo_intervencion = fields.Float(string='Tiempo de Intervención')    
    prensa = fields.Selection([('si', 'Sí'), ('no', 'No')], string='Prensa')
    data_politica = fields.Char(string='Data Política')    
    mesa_tecnica_ids = fields.One2many('mz_convoy.mesa_tecnica', 'evento_id', string='Miembros Mesa Técnica')    
    sillas_requeridas = fields.Integer(string='Sillas Requeridas')
    carpas_requeridas = fields.Integer(string='Carpas Requeridas')
    responsable_convoy = fields.Many2one(string='Responsable del Convoy', comodel_name='hr.employee', ondelete='restrict')
    responsables_avanzada = fields.Many2many('hr.employee', string='Responsables de Avanzada')
    responsable_socializacion = fields.Many2one(string='Responsable de Socialización', comodel_name='hr.employee', ondelete='restrict')
    responsable_mesa_tecnica = fields.Many2one(string='Responsable de Mesa Técnica', comodel_name='hr.employee', ondelete='restrict')
    responsable_convocatoria = fields.Many2one(string='Responsable de Convocatoria del Cantón', comodel_name='hr.employee', ondelete='restrict')
    autoridades_externa_ids = fields.One2many('mz_convoy.autoridades', 'convoy_id', string='Autoridades')
    alertas_quejas_ids = fields.One2many('mz_convoy.alertas_quejas', 'convoy_id', string='Alertas/Quejas')
    mostrar_boton_publicar = fields.Boolean(compute='_compute_mostrar_boton_publicar', compute_sudo=True)
    mostrar_bot_retirar_public = fields.Boolean(compute='_compute_mostrar_bot_retirar_public', compute_sudo=True)
    can_edit_services = fields.Boolean(compute='_compute_can_edit_services')    
    state = fields.Selection([('borrador', 'Borrador'),('aprobado', 'Aprobado'),('fin', 'Finalizado')], string='Estado', default='borrador', tracking=True)  
    operadores_ids = fields.Many2many(string='Operadores', comodel_name='hr.employee', relation='convoy_operador_rel', 
                                      column1='convoy_id', column2='employee_id',domain="[('user_id','!=',False)]")
    colaboradores_ids = fields.Many2many(string='Colaboradores', comodel_name='hr.employee', relation='mz_convoy_colaborador_rel', 
                                      column1='convoy_id', column2='colaborador_id')

    ficha_evento_legalizada = fields.Many2many(comodel_name='ir.attachment', relation='pf_mz_convoy_ficha_evento_legalizada', 
                                      column1='convoy_id', column2='ficha_id', string='Ficha Evento Legalizada')
    ficha_implantacion_legalizada = fields.Many2many(comodel_name='ir.attachment', relation='pf_mz_convoy_ficha_impantacion_legalizada', 
                                      column1='convoy_id', column2='ficha_id', string='Ficha Implantación Legalizada')
    beneficiario_ids = fields.One2many('mz_convoy.beneficiario', 'convoy_id', string='Beneficiarios')
    beneficiario_count = fields.Integer( string='Número de Beneficiarios', compute='_compute_beneficiario_count')
    beneficiarios_masivo_count = fields.Integer(string='Masivo', compute='_compute_beneficiarios_count')
    beneficiarios_asistencia_count = fields.Integer(string='Asistencia', compute='_compute_beneficiarios_count')
    beneficiarios_socioeconomico_count = fields.Integer(string='Socioeconómico', compute='_compute_beneficiarios_count')

    @api.depends('beneficiario_ids', 'beneficiario_ids.tipo_registro')
    def _compute_beneficiarios_count(self):
        for record in self:
            beneficiarios = record.beneficiario_ids
            record.beneficiarios_masivo_count = len(beneficiarios.filtered(lambda b: b.tipo_registro == 'masivo'))
            record.beneficiarios_asistencia_count = len(beneficiarios.filtered(lambda b: b.tipo_registro == 'asistencia'))
            record.beneficiarios_socioeconomico_count = len(beneficiarios.filtered(lambda b: b.tipo_registro == 'socioeconomico'))

    def action_view_beneficiarios_masivo(self):
        self.ensure_one()
        return {
            'name': 'Beneficiarios Masivos',
            'view_mode': 'tree,form',
            'res_model': 'mz_convoy.beneficiario',
            'type': 'ir.actions.act_window',
            'domain': [('convoy_id', '=', self.id), ('tipo_registro', '=', 'masivo')],
            'context': {
                'default_convoy_id': self.id,
                'default_tipo_registro': 'masivo',
                'form_view_initial_mode': 'readonly',  # Formulario en modo lectura
                'create': False,  # Deshabilita creación
                'edit': False,    # Deshabilita edición
                'delete': False   # Deshabilita eliminación
            },
            'target': 'current',
        }

    def action_view_beneficiarios_asistencia(self):
        self.ensure_one()
        return {
            'name': 'Beneficiarios por Asistencia',
            'view_mode': 'tree,form',
            'res_model': 'mz_convoy.beneficiario',
            'type': 'ir.actions.act_window',
            'domain': [('convoy_id', '=', self.id), ('tipo_registro', '=', 'asistencia')],
            'context': {
                'default_convoy_id': self.id,
                'default_tipo_registro': 'asistencia',
                'form_view_initial_mode': 'readonly',
                'create': False,
                'edit': False,
                'delete': False
            },
            'target': 'current',
        }

    def action_view_beneficiarios_socioeconomico(self):
        self.ensure_one()
        return {
            'name': 'Beneficiarios Socioeconómico',
            'view_mode': 'tree,form',
            'res_model': 'mz_convoy.beneficiario',
            'type': 'ir.actions.act_window',
            'domain': [('convoy_id', '=', self.id), ('tipo_registro', '=', 'socioeconomico')],
            'context': {
                'default_convoy_id': self.id,
                'default_tipo_registro': 'socioeconomico',
                'form_view_initial_mode': 'readonly',
                'create': False,
                'edit': False,
                'delete': False
            },
            'target': 'current',
        }

    @api.depends('beneficiario_ids')
    def _compute_beneficiario_count(self):
        for record in self:
            record.beneficiario_count = len(record.beneficiario_ids)
    
    @api.constrains('ficha_evento_legalizada', 'ficha_implantacion_legalizada')
    def _check_fichas_legalizadas(self):
        for record in self:
            if not record.ficha_evento_legalizada or not record.ficha_implantacion_legalizada:
                raise UserError("Es obligatorio adjuntar documentos en  fichas legalizadas")
    
        
    @api.model
    def asignacion_permiso_operador(self):
        current_datetime = datetime.now() - timedelta(hours=5)
        today = current_datetime.date()  # Convertir a date
        convoys = self.search([('state', '=', 'aprobado'), ('fecha_evento', '=', today)])        
        grupo_operador = self.env.ref('manzana_convoy.group_mz_convoy_operador')      
        grupo_coordinador = self.env.ref('manzana_convoy.group_mz_convoy_operador')   
        for convoy in convoys:           
            for empleado in convoy.operadores_ids:                
                if empleado.user_id:  # Verificamos que el empleado tenga usuario
                    empleado.user_id.write({'groups_id': [(4, grupo_operador.id)]})
            convoy.director_coordinador.user_id.write({'groups_id': [(4, grupo_coordinador.id)]})

    def aprobar_convoy(self):
        self.write({'state': 'aprobado'})

    def action_finalizar(self):
        grupo_operador = self.env.ref('manzana_convoy.group_mz_convoy_operador')       
        grupo_coordinador = self.env.ref('manzana_convoy.group_mz_convoy_operador')  
        for record in self:
            record.director_coordinador.user_id.write({'groups_id': [(3, grupo_coordinador.id)]})
            # Quitar permisos a operadores
            for empleado in record.operadores_ids:
                if empleado.user_id:
                    empleado.user_id.write({
                        'groups_id': [(3, grupo_operador.id)]  # Remueve el grupo
                    })

            
            # Cambiar estado a finalizado
            record.write({
                'state': 'fin'
            })

    

    @api.depends('programa_id')
    def _compute_can_edit_services(self):
        for record in self:
            record.can_edit_services = bool(record.id)

    @api.depends('programa_id.if_publicado', 'programa_id.active')
    def _compute_mostrar_boton_publicar(self):
        for record in self:
            record.mostrar_boton_publicar = (
                record.programa_id.active and 
                not record.programa_id.if_publicado
            )

    @api.depends('programa_id.if_publicado', 'programa_id.active')
    def _compute_mostrar_bot_retirar_public(self):
        for record in self:
            record.mostrar_bot_retirar_public = (
                record.programa_id.active and 
                record.programa_id.if_publicado
            )

    # Opción 1: Redirigir al registro padre
    def action_activar(self):
        return self.programa_id.action_activar()

    def action_publish(self):
        return self.programa_id.action_publish()

    def action_unpublish_wizard(self):
        return self.programa_id.action_unpublish_wizard()

    @api.depends('hora_inicio', 'hora_fin')
    def _compute_duracion(self):
        for record in self:
            inicio = record.hora_inicio or 0.0
            fin = record.hora_fin or 0.0            
            if not fin or (fin - inicio) < 0:
                record.duracion = '0 horas'
                continue            
            diferencia = fin - inicio
            horas_enteras = int(diferencia)
            minutos = int((diferencia - horas_enteras) * 60)            
            if minutos == 0:
                record.duracion = f'{horas_enteras} horas'
            elif minutos == 30:
                record.duracion = f'{horas_enteras} horas y media'
            else:
                record.duracion = f'{horas_enteras} horas y {minutos} minutos'

    @api.depends('fecha_evento')
    def _compute_dia_semana(self):
        for record in self:
            if record.fecha_evento:
                dias_semana = {
                    0: 'Lunes',
                    1: 'Martes',
                    2: 'Miércoles',
                    3: 'Jueves',
                    4: 'Viernes',
                    5: 'Sábado',
                    6: 'Domingo'
                }
                dia_numero = record.fecha_evento.weekday()
                record.dia_semana = dias_semana[dia_numero]
            else:
                record.dia_semana = False

class ConvoyMiembroMesaTecnica(models.Model):
    _name = 'mz_convoy.mesa_tecnica'
    _description = 'Miembro de Mesa Técnica'

    evento_id = fields.Many2one('mz.convoy', string='Evento')
    nombre = fields.Char(string='Nombre', required=True)
    cargo_institucion_id = fields.Many2one('mz.items', string='Cargo/Institución',
                                             domain=lambda self: [('catalogo_id', '=', self.env.ref('manzana_convoy.catalogo_instituciones_publicas').id)])
    contacto = fields.Char(string='Número de Contacto')


class ConvoyAutoriades(models.Model):
    _name = 'mz_convoy.autoridades'
    _description = 'Autoridades'
    
    convoy_id = fields.Many2one(string='Convoy', comodel_name='mz.convoy', ondelete='restrict')    
    nombre = fields.Char(string='Nombre', required=True)

class ConvoyAlertasQuejas(models.Model):
    _name = 'mz_convoy.alertas_quejas'
    _description = 'Alertas/Quejas'
    
    convoy_id = fields.Many2one(string='Convoy', comodel_name='mz.convoy', ondelete='restrict')    
    nombre = fields.Char(string='Nombre', required=True)
    