from odoo import models, fields, api
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError
import logging


class FichaEvento(models.Model):
    _name = 'mz.convoy'
    _description = 'Ficha de Evento'
    _inherits = {'pf.programas': 'programa_id'} 
    _inherit = ['mail.thread', 'mail.activity.mixin'] 

    # Corrección del campo programa_id para apuntar al modelo correcto
    programa_id = fields.Many2one('pf.programas', string='Programa', ondelete='restrict',  required=True, auto_join=True)
    institucion_anfitriona = fields.Char(string='Institución Anfitriona') 
    director_coordinador = fields.Many2one(string='Coordinador Responsable', comodel_name='hr.employee', ondelete='restrict', required=True)       
    # El resto de los campos permanecen igual
    fecha_inicio_evento = fields.Date(string='Fecha Inicio',required=True)
    fecha_hasta_evento = fields.Date(string='Fecha Fin',required=True)
    dia_semana = fields.Char(string='Día', compute='_compute_dia_semana', store=True)
    lugar = fields.Char(string='Lugar')
    hora_inicio = fields.Float(string='Hora Inicio')
    hora_fin = fields.Float(string='Hora Fin')
    duracion = fields.Char(string='Duración', compute='_compute_duracion', store=True)    
    tipo_evento = fields.Many2one('pf.items', string='Tipo Evento', domain=lambda self: [('catalogo_id', '=', self.env.ref('manzana_convoy.catalogo_tipo_evento').id)])
    formato_evento = fields.Char(string='Formato de Evento')
    numero_asistentes = fields.Integer(string='Número de Asistentes')
    codigo_vestimenta = fields.Char(string='Código de Vestimenta')   
    participacion_prefecta = fields.Many2one('pf.items', string='Participación  Prefecta', domain=lambda self: [('catalogo_id', '=', self.env.ref('manzana_convoy.catalogo_participacion_especifica').id)])
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
    state = fields.Selection([('borrador', 'Borrador'),('aprobado', 'Aprobado'),('ejecutando', 'Ejecutando'),('fin', 'Finalizado')], string='Estado', default='borrador', tracking=True)  
    operadores_ids = fields.Many2many(string='Operadores', comodel_name='hr.employee', relation='convoy_operador_rel', 
                                      column1='convoy_id', column2='employee_id',domain="[('user_id','!=',False)]")
    colaboradores_ids = fields.Many2many(string='Colaboradores', comodel_name='hr.employee', relation='mz_convoy_colaborador_rel', 
                                      column1='convoy_id', column2='colaborador_id') 
    permisos_ids = fields.One2many('mz_convoy.permisos', 'convoy_id', string='Permisos Personal Convoy')
   
    ficha_evento_legalizada = fields.Binary(string="Ficha Evento Legalizada", attachment=True)
    ficha_evento_legalizada_name = fields.Char(string="Nombre Ficha Evento")

    ficha_implantacion_legalizada = fields.Binary(string="Ficha Implantación Legalizada", attachment=True)
    ficha_implantacion_legalizada_name = fields.Char(string="Nombre Ficha Implantación")

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

    @api.depends('fecha_inicio_evento', 'fecha_hasta_evento')
    def _compute_dia_semana(self):
        for record in self:
            if record.fecha_inicio_evento and record.fecha_hasta_evento:
                dias_semana = {
                    0: 'Lunes',
                    1: 'Martes',
                    2: 'Miércoles',
                    3: 'Jueves',
                    4: 'Viernes',
                    5: 'Sábado',
                    6: 'Domingo'
                }                
                # Si las fechas son iguales, solo mostrar el día
                if record.fecha_inicio_evento == record.fecha_hasta_evento:
                    record.dia_semana = dias_semana[record.fecha_inicio_evento.weekday()]
                else:
                    # Si son diferentes, mostrar el rango
                    dia_inicio = dias_semana[record.fecha_inicio_evento.weekday()]
                    dia_fin = dias_semana[record.fecha_hasta_evento.weekday()]
                    record.dia_semana = f'De {dia_inicio} a {dia_fin}'
            else:
                record.dia_semana = False



    def action_aprobar_convoy(self):
        """Método para aprobar convoy"""
        self.ensure_one()
        
        # Validar fecha de inicio
        fecha_actual = (fields.Datetime.now() - timedelta(hours=5)).date()
        if self.fecha_inicio_evento < fecha_actual:
            raise UserError("No se puede aprobar el convoy. La fecha de inicio debe ser mayor a la fecha actual.")
        
        # Validaciones adicionales que ya tenías
        if not self.director_coordinador:
            raise UserError("No se puede aprobar el convoy sin un coordinador asignado")
            
        if not self.director_coordinador.user_id:
            raise UserError(f"El coordinador {self.director_coordinador.name} no tiene un usuario del sistema asignado")
        
        try:
            # Asignar permiso de coordinador
            grupo_coordinador = self.env.ref('manzana_convoy.group_mz_convoy_coordinador')
            self.director_coordinador.user_id.write({
                'groups_id': [(4, grupo_coordinador.id)]
            })
            
            # Cambiar estado
            self.write({'state': 'aprobado'})
            
            # Mensaje en el chatter
            mensaje = f"""
                ✅ Convoy Aprobado

                - Fecha de aprobación: {fields.Datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
                - Fecha inicio evento: {self.fecha_inicio_evento.strftime('%d/%m/%Y')}
                - Fecha fin evento: {self.fecha_hasta_evento.strftime('%d/%m/%Y')}
                - Coordinador asignado: {self.director_coordinador.name}
                """
            self.message_post(
                body=mensaje,
                message_type='notification',
                subtype_xmlid='mail.mt_note'
            )
            
        except Exception as e:
            raise UserError(f"Error al aprobar convoy: {str(e)}")

    def action_ejecutar_convoy(self):
        """Método para ejecutar convoy y asignar permisos a operadores y prestadores"""
        self.ensure_one()        
        if not self.servicio_ids:
            raise UserError("Debe existir al menos un servicio asignado al convoy")
        if not self.operadores_ids:
            raise UserError("Debe existir al menos un operador asignado al convoy")
            
        if self.state != 'aprobado':
            raise UserError("Solo se pueden ejecutar convoyes en estado aprobado")
            
        fecha_actual = (fields.Datetime.now() - timedelta(hours=5)).date()
        if self.fecha_inicio_evento != fecha_actual:
            raise UserError("Solo se pueden ejecutar convoyes en su fecha de inicio programada")

        try:
            grupo_base = self.env.ref('base.group_user')
            grupo_operador = self.env.ref('manzana_convoy.group_mz_convoy_operador')
            grupo_prestador = self.env.ref('manzana_convoy.group_mz_convoy_prestador_servicio')
            grupo_coordinador = self.env.ref('manzana_convoy.group_mz_convoy_coordinador')
            
            if not grupo_operador or not grupo_prestador or not grupo_coordinador:
                raise UserError("No se encontraron los grupos necesarios")
            # Procesar coordinador
            if self.director_coordinador and self.director_coordinador.user_id:
                valores_permisos = {'convoy_id': self.id, 'user_id': self.director_coordinador.user_id.id, 'permisos_originales': [(6, 0, self.director_coordinador.user_id.groups_id.ids)]}                
                self.env['mz_convoy.permisos'].create(valores_permisos)                
                self.director_coordinador.user_id.write({'groups_id': [(6, 0, [grupo_base.id]), (4, grupo_coordinador.id)]})
            for operador in self.operadores_ids:
                if not operador.user_id:
                    continue
                valores_permisos = {'convoy_id': self.id, 'user_id': operador.user_id.id, 'permisos_originales': [(6, 0, operador.user_id.groups_id.ids)]}                
                self.env['mz_convoy.permisos'].create(valores_permisos)                
                operador.user_id.write({
                    'groups_id': [(6, 0, [grupo_base.id]), (4, grupo_operador.id)]})
            for servicio in self.servicio_ids:
                for prestador in servicio.personal_ids:
                    if not prestador.user_id:
                        continue
                    permiso_existente = self.env['mz_convoy.permisos'].search([('convoy_id', '=', self.id), ('user_id', '=', prestador.user_id.id)])
                    if not permiso_existente:
                        valores_permisos = {'convoy_id': self.id, 'user_id': prestador.user_id.id, 'permisos_originales': [(6, 0, prestador.user_id.groups_id.ids)]}
                        self.env['mz_convoy.permisos'].create(valores_permisos)
                    prestador.user_id.write({'groups_id': [(6, 0, [grupo_base.id]), (4, grupo_prestador.id)]})
            # Actualizar horarios
            horarios = self.env['mz.genera.planificacion.servicio'].search([('convoy_id', '=', self.id)])
            if horarios:
                horarios.write({'estado': 'confirmado'})
            self.write({'state': 'ejecutando'})
            mensaje = f"""
            ▶️ Convoy Iniciado
            - Fecha de inicio: {fields.Datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
            - Fecha programada inicio: {self.fecha_inicio_evento.strftime('%d/%m/%Y')}
            - Fecha programada fin: {self.fecha_hasta_evento.strftime('%d/%m/%Y')}
            - Operadores asignados: {len(self.operadores_ids)}
            - Se han guardado y modificado los permisos de operadores y prestadores de servicio
            """            
            self.message_post(body=mensaje, message_type='notification', subtype_xmlid='mail.mt_note')
        except Exception as e:
            raise UserError(f"Error al ejecutar convoy: {str(e)}")
   
    def action_finalizar_manual(self, es_automatico=False):
        """Método para finalizar convoy"""
        self.ensure_one()
        
        if self.state != 'ejecutando':
            if es_automatico:
                return
            raise UserError("Solo se pueden finalizar convoyes en estado ejecutando")

        if not es_automatico:
            fecha_actual = (fields.Datetime.now() - timedelta(hours=5)).date()
            if self.fecha_hasta_evento > fecha_actual:
                raise UserError("Solo se pueden finalizar convoyes en su fecha de fin programada")

        try:
            for permiso in self.permisos_ids:
                if permiso.user_id:
                    permiso.user_id.write({'groups_id': [(6, 0, permiso.permisos_originales.ids)]})
            self.permisos_ids.unlink()
            self.write({'state': 'fin'})
            fecha_hora_actual = fields.Datetime.now() - timedelta(hours=5)
            titulo = "🔄 Convoy Finalizado Automáticamente" if es_automatico else "✅ Convoy Finalizado Manualmente"
            mensaje = f"""
            {titulo}
            - Fecha de finalización: {fecha_hora_actual.strftime('%d/%m/%Y %H:%M:%S')}
            - Fecha programada fin: {self.fecha_hasta_evento.strftime('%d/%m/%Y')}
            - Se han restaurado los permisos originales de todos los usuarios
            """
            self.message_post(body=mensaje, message_type='notification', subtype_xmlid='mail.mt_note')

        except Exception as e:
            error_msg = f"Error al finalizar convoy: {str(e)}"
            if es_automatico:
                logger.error(error_msg)
                return
            raise UserError(error_msg)
        
        def _cron_verificar_fecha_finalizacion(self):
            """Método para verificar y finalizar convoyes por fecha"""
            fecha_actual = (fields.Datetime.now() - timedelta(hours=5)).date()
            # Buscar convoyes que deben finalizarse
            convoyes_para_finalizar = self.search([
                ('state', '=', 'ejecutando'),
                ('fecha_hasta_evento', '=', fecha_actual)
            ])
            
            for convoy in convoyes_para_finalizar:
                convoy.action_finalizar_manual(es_automatico=True)

  
class ConvoyMiembroMesaTecnica(models.Model):
    _name = 'mz_convoy.mesa_tecnica'
    _description = 'Miembro de Mesa Técnica'

    evento_id = fields.Many2one('mz.convoy', string='Evento')
    nombre = fields.Char(string='Nombre', required=True)
    cargo_institucion_id = fields.Many2one('pf.items', string='Cargo/Institución',
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
    