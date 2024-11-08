from odoo import models, fields, api
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError



class ConvoyBeneficiario(models.Model):
    _name = 'mz_convoy.convoy_beneficiario'
    _description = 'Registro Masivo de Beneficiarios Convoy'

    beneficiario_id = fields.Many2one('mz_convoy.beneficiario', string='Beneficiario', ondelete='restrict')
    tipo_registro = fields.Selection([('masivo', 'Registro Masivo'), ('asistencia', 'Registro por Asistencia'), ('socioeconomico', 'Registro Socioeconómico')], 
                                     string='Tipo de Registro', required=True, default='masivo')
    # Campos comunes
    convoy_id = fields.Many2one('mz.convoy', string='Convoy', required=True)    
    programa_id = fields.Many2one(string='Programa', comodel_name='pf.programas', ondelete='restrict', related='convoy_id.programa_id', readonly=True)    
    num_documento = fields.Char('Número de Documento', required=True)
    nombres = fields.Char('Nombres', required=True)
    apellidos = fields.Char('Apellidos', required=True)
    es_extranjero = fields.Boolean('¿Es Migrante Extranjero?')
    pais = fields.Char('País', default='Ecuador')
    celular = fields.Char('Celular')
    operadora_id = fields.Many2one('mz_convoy.items', string='Operadora', domain=lambda self: [('catalogo_id', '=', self.env.ref('manzana_convoy.catalogo_operadoras').id)])
    # Campos de asistencia
    fecha_nacimiento = fields.Date('Fecha de Nacimiento')
    edad = fields.Integer('Edad', compute='_compute_edad', store=True)
    estado_civil_id = fields.Many2one('mz_convoy.items', string='Estado Civil', domain=lambda self: [('catalogo_id', '=', self.env.ref('manzana_convoy.catalogo_estado_civil').id)])
    genero_id = fields.Many2one('mz_convoy.items', string='Género', domain=lambda self: [('catalogo_id', '=', self.env.ref('manzana_convoy.catalogo_genero').id)])
    canton = fields.Char('Cantón')
    parroquia = fields.Char('Parroquia')
    direccion_domicilio = fields.Char('Dirección de domicilio')
    correo_electronico = fields.Char('Correo Electrónico')
    tiene_discapacidad = fields.Boolean('¿Tiene usted alguna discapacidad?')
    recibe_bono = fields.Boolean('¿Recibe algún tipo de bono?')
    tipo_discapacidad_id = fields.Many2one('mz_convoy.items', string='Tipo de Discapacidad', 
                                           domain=lambda self: [('catalogo_id', '=', self.env.ref('manzana_convoy.catalogo_convoy_tipo_discapacidad').id)])
    nivel_instruccion_id = fields.Many2one('mz_convoy.items', string='Nivel de Instrucción',
                                           domain=lambda self: [('catalogo_id', '=', self.env.ref('manzana_convoy.catalogo_nivel_instruccion').id)])
    situacion_laboral_id = fields.Many2one('mz_convoy.items', string='Situación Laboral',
                                           domain=lambda self: [('catalogo_id', '=', self.env.ref('manzana_convoy.catalogo_situacion_laboral').id)])
    tipo_vivienda_id = fields.Many2one('mz_convoy.items', string='La vivienda donde habita es?', 
                                       domain=lambda self: [('catalogo_id', '=', self.env.ref('manzana_convoy.catalogo_tipo_vivienda').id)])
    tiene_internet = fields.Selection([('si', 'SI'), ('no', 'NO')], string='¿Su hogar cuenta con internet?')
    tiene_agua_potable = fields.Selection([('si', 'SI'), ('no', 'NO')], string='¿La vivienda donde habita tiene servicio de agua potable por tubería?')
    tiene_luz_electrica = fields.Selection([('si', 'SI'), ('no', 'NO')], string='¿La vivienda donde habita cuenta con luz eléctrica?')
    tiene_alcantarillado = fields.Selection([('si', 'SI'), ('no', 'NO')], string='¿La vivienda donde habita tiene servicio de alcantarillado?')
    es_cuidador = fields.Selection([('si', 'SI'), ('no', 'NO')], string='¿Es cuidador/a?')
    hora_tarea_domestica = fields.Integer(string='Horas a tareas domésticas',)
    sostiene_hogar = fields.Selection([('si', 'SI'), ('no', 'NO')], string='¿Usted sostiene económicamente su hogar?')
    enfermedad_catastrofica = fields.Selection([('si', 'SI'), ('no', 'NO')], string='¿Padece alguna enfermedad catastrófica?')
    hombres_hogar = fields.Integer(string='¿Cuántos hombres viven en el hogar(contando niños)?',)
    mujer_hogar = fields.Integer(string='¿Cuántos mujeres viven en el hogar(contando niñas)?',)
    ninos_menores = fields.Integer(string='¿Cuántos niños menores de edad habitan en el hogar?',)
    ninos_5_estudiando = fields.Integer(string='¿Cuántos niños mayores de 5 años que habitan en el hogar estan estudiando?',)
    mujeres_embarazadas = fields.Integer(string='¿Cuántas mujeres embarazadas habitan en su hogar?', default=0)
    mujeres_embarazadas_chequeos = fields.Integer(string='¿Cuántas mujeres embarazadas que habitan en el hogar asisten a chequeos médicos?', default=0)
    mujeres_embarazadas_menores = fields.Integer(string='¿Cuántas de las mujeres embarazadas son menores de 18 años?', default=0)
    mayor_65 = fields.Selection([('si', 'SI'), ('no', 'NO')], string='¿Hay mayores de 65 años viviendo en su hogar?')
    discapacidad_hogar = fields.Selection([('si', 'SI'), ('no', 'NO')], string='¿Hay personas con discapacidad viviendo en su hogar?')
    tiene_discapacidad_hogar = fields.Selection([('si', 'SI'),('no', 'NO')], string='¿Hay personas con discapacidad viviendo en su hogar?', default='no')
    tipo_discapacidad_hogar_id = fields.Many2one('mz_convoy.items', string='¿Qué tipo de discapacidad tiene?',
                                                 domain=lambda self: [('catalogo_id', '=', self.env.ref('manzana_convoy.catalogo_convoy_tipo_discapacidad').id)])
    servicio_id = fields.Many2one('mz.asignacion.servicio', string='Servicio', domain="[('programa_id', '=', programa_id)]",)  
    

    @api.onchange('tiene_discapacidad_hogar')
    def _onchange_tiene_discapacidad_hogar(self):
        if self.tiene_discapacidad_hogar == 'no':
            self.tipo_discapacidad_hogar_id = False
        elif self.tiene_discapacidad_hogar == 'si' and not self.tipo_discapacidad_hogar_id:
            # Buscar el registro "NINGUNA" por defecto
            ninguna = self.env['mz_convoy.items'].search([
                ('catalogo_id', '=', self.env.ref('manzana_convoy.catalogo_convoy_tipo_discapacidad').id),
                ('name', '=', 'NINGUNA')
            ], limit=1)
            if ninguna:
                self.tipo_discapacidad_hogar_id = ninguna.id 

    @api.onchange('mujeres_embarazadas_chequeos', 'mujeres_embarazadas_menores')
    def _onchange_field(self):
        if self.mujeres_embarazadas_chequeos:
            if self.mujeres_embarazadas and self.mujeres_embarazadas_chequeos > self.mujeres_embarazadas:
                raise UserError('El número de mujeres embarazadas que asisten a chequeos no puede ser mayor al número total de mujeres embarazadas.')
                
        if self.mujeres_embarazadas_menores:
            if self.mujeres_embarazadas and self.mujeres_embarazadas_menores > self.mujeres_embarazadas:
                raise UserError('El número de mujeres embarazadas menores de 18 años no puede ser mayor al número total de mujeres embarazadas.')

    @api.depends('fecha_nacimiento')
    def _compute_edad(self):
        for record in self:
            if record.fecha_nacimiento:
                today = date.today()
                record.edad = today.year - record.fecha_nacimiento.year - (
                    (today.month, today.day) < (record.fecha_nacimiento.month, record.fecha_nacimiento.day)
                )
            else:
                record.edad = 0

    @api.constrains('num_documento')
    def _check_documento(self):
        for record in self:
            if not record.es_extranjero and record.pais == 'Ecuador':
                if not record.num_documento.isdigit() or len(record.num_documento) != 10:
                    raise UserError('El número de documento debe tener 10 dígitos para ciudadanos ecuatorianos')

    _sql_constraints = [
        ('beneficiario_convoy_uniq', 
         'UNIQUE(num_documento, convoy_id, tipo_registro)',
         'Este beneficiario ya está registrado en este convoy con este tipo de registro.')
    ]

    @api.model
    def create(self, vals):
        # Primero buscar si existe el beneficiario
        beneficiario = self.env['mz_convoy.beneficiario'].search([
            ('num_documento', '=', vals.get('num_documento'))
        ], limit=1)

        # Inicializar beneficiario_vals con campos comunes
        beneficiario_vals = {
            'num_documento': vals.get('num_documento'),
            'nombres': vals.get('nombres'),
            'apellidos': vals.get('apellidos'),
            'es_extranjero': vals.get('es_extranjero'),
            'pais': vals.get('pais'),
            'celular': vals.get('celular'),
            'operadora_id': vals.get('operadora_id'),
            'tipo_discapacidad_id': vals.get('tipo_discapacidad_id'),
            'nivel_instruccion_id': vals.get('nivel_instruccion_id'),
            'situacion_laboral_id': vals.get('situacion_laboral_id'),
            'tipo_vivienda_id': vals.get('tipo_vivienda_id'),
            'tiene_internet': vals.get('tiene_internet'),
            'tiene_agua_potable': vals.get('tiene_agua_potable'),
            'tiene_luz_electrica': vals.get('tiene_luz_electrica'),
            'tiene_alcantarillado': vals.get('tiene_alcantarillado'),
            'es_cuidador': vals.get('es_cuidador'),
            'hora_tarea_domestica': vals.get('hora_tarea_domestica'),
            'sostiene_hogar': vals.get('sostiene_hogar'),
            'enfermedad_catastrofica': vals.get('enfermedad_catastrofica'),
            'hombres_hogar': vals.get('hombres_hogar'),
            'mujer_hogar': vals.get('mujer_hogar'),
            'ninos_menores': vals.get('ninos_menores'),
            'ninos_5_estudiando': vals.get('ninos_5_estudiando'),
            'mujeres_embarazadas': vals.get('mujeres_embarazadas'),
            'mujeres_embarazadas_chequeos': vals.get('mujeres_embarazadas_chequeos'),
            'mujeres_embarazadas_menores': vals.get('mujeres_embarazadas_menores'),
            'mayor_65': vals.get('mayor_65'),
            'discapacidad_hogar': vals.get('discapacidad_hogar'),
            'tiene_discapacidad_hogar': vals.get('tiene_discapacidad_hogar'),
            'tipo_discapacidad_hogar_id': vals.get('tipo_discapacidad_hogar_id'),
        }

        # Agregar campos adicionales si es registro por asistencia
        if vals.get('tipo_registro') == 'asistencia':
            beneficiario_vals.update({
                'fecha_nacimiento': vals.get('fecha_nacimiento'),
                'estado_civil_id': vals.get('estado_civil_id'),
                'genero_id': vals.get('genero_id'),
                'canton': vals.get('canton'),
                'parroquia': vals.get('parroquia'),
                'direccion_domicilio': vals.get('direccion_domicilio'),
                'correo_electronico': vals.get('correo_electronico'),
                'tiene_discapacidad': vals.get('tiene_discapacidad'),
                'recibe_bono': vals.get('recibe_bono'),
            })

        if not beneficiario:
            beneficiario = self.env['mz_convoy.beneficiario'].create(beneficiario_vals)
        else:
            beneficiario.write(beneficiario_vals)

        vals['beneficiario_id'] = beneficiario.id
        record = super(ConvoyBeneficiario, self).create(vals)

        if record.servicio_id:
            self.env['mz.agendar_servicio'].create({
                'state': 'borrador',
                'modulo_id': self.env.ref('prefectura_base.modulo_2').id,
                'beneficiario_id': record.beneficiario_id.id,
                'programa_id': record.programa_id.id,
                'servicio_id': record.servicio_id.id,
                'fecha_solicitud': fields.Date.today(),  # Cambiado para usar la fecha actual
                'personal_id': record.servicio_id.personal_ids[0].id if record.servicio_id.personal_ids else False,
            })

        return record

    
    def write(self, vals):
        result = super(ConvoyBeneficiario, self).write(vals)
        for record in self:
            # Actualización del beneficiario
            beneficiario = record.beneficiario_id
            if beneficiario:
                update_vals = {
                    'num_documento': record.num_documento,
                    'nombres': record.nombres,
                    'apellidos': record.apellidos,
                    'es_extranjero': record.es_extranjero,
                    'pais': record.pais,
                    'celular': record.celular,
                    'operadora_id': record.operadora_id.id if record.operadora_id else False,
                    'tipo_discapacidad_id': record.tipo_discapacidad_id.id if record.tipo_discapacidad_id else False,
                    'nivel_instruccion_id': record.nivel_instruccion_id.id if record.nivel_instruccion_id else False,
                    'situacion_laboral_id': record.situacion_laboral_id.id if record.situacion_laboral_id else False,
                    'tipo_vivienda_id': record.tipo_vivienda_id.id if record.tipo_vivienda_id else False,
                    'tiene_internet': record.tiene_internet,
                    'tiene_agua_potable': record.tiene_agua_potable,
                    'tiene_luz_electrica': record.tiene_luz_electrica,
                    'tiene_alcantarillado': record.tiene_alcantarillado,
                    'es_cuidador': record.es_cuidador,
                    'hora_tarea_domestica': record.hora_tarea_domestica,
                    'sostiene_hogar': record.sostiene_hogar,
                    'enfermedad_catastrofica': record.enfermedad_catastrofica,
                    'hombres_hogar': record.hombres_hogar,
                    'mujer_hogar': record.mujer_hogar,
                    'ninos_menores': record.ninos_menores,
                    'ninos_5_estudiando': record.ninos_5_estudiando,
                    'mujeres_embarazadas': record.mujeres_embarazadas,
                    'mujeres_embarazadas_chequeos': record.mujeres_embarazadas_chequeos,
                    'mujeres_embarazadas_menores': record.mujeres_embarazadas_menores,
                    'mayor_65': record.mayor_65,
                    'discapacidad_hogar': record.discapacidad_hogar,
                    'tiene_discapacidad_hogar': record.tiene_discapacidad_hogar,
                    'tipo_discapacidad_hogar_id': record.tipo_discapacidad_hogar_id.id if record.tipo_discapacidad_hogar_id else False,
                }
                if record.tipo_registro == 'asistencia':
                    update_vals.update({
                        'fecha_nacimiento': record.fecha_nacimiento,
                        'estado_civil_id': record.estado_civil_id.id if record.estado_civil_id else False,
                        'genero_id': record.genero_id.id if record.genero_id else False,
                        'canton': record.canton,
                        'parroquia': record.parroquia,
                        'direccion_domicilio': record.direccion_domicilio,
                        'correo_electronico': record.correo_electronico,
                        'tiene_discapacidad': record.tiene_discapacidad,
                        'recibe_bono': record.recibe_bono,
                    })
                beneficiario.write(update_vals)

            # Creación del servicio si se actualizó el campo servicio_id
            if 'servicio_id' in vals and record.servicio_id:
                self.env['mz.agendar_servicio'].create({
                    'state': 'borrador',
                    'modulo_id': self.env.ref('prefectura_base.modulo_2').id,
                    'beneficiario_id': record.beneficiario_id.id,
                    'programa_id': record.programa_id.id,
                    'servicio_id': record.servicio_id.id,
                    'fecha_solicitud': fields.Date.today(),  # Usando la fecha actual
                    'personal_id': record.servicio_id.personal_ids[0].id if record.servicio_id.personal_ids else False,
                })

        return result