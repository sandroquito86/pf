# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date
from dateutil.relativedelta import relativedelta


class ConvoyBeneficiarioWizard(models.TransientModel):
    _name = 'mz_convoy.beneficiario_wizard'
    _description = 'Wizard para registro de beneficiarios de Convoy'

    # Campos de control
    convoy_id = fields.Many2one('mz.convoy', string='Convoy', required=True)
    beneficiario_id = fields.Many2one('mz.beneficiario', string='Beneficiario')
    tipo_registro = fields.Selection([
        ('masivo', 'Registro Masivo'),
        ('asistencia', 'Registro por Asistencia'),
        ('socioeconomico', 'Registro Socioeconómico')
    ], string='Tipo de Registro', required=True, default='masivo')
    
    # Campos comunes
    programa_id = fields.Many2one('pf.programas', related='convoy_id.programa_id', readonly=True)
    tipo_documento = fields.Selection([
        ('dni', 'DNI'),
        ('pasaporte', 'Pasaporte'),
        ('carnet_extranjeria', 'Carnet de Extranjería')
    ], string='Tipo de Documento', required=True, tracking=True)
    numero_documento = fields.Char('Número de Documento', required=True)
    apellido_paterno = fields.Char(string='Apellido Paterno')
    apellido_materno = fields.Char(string='Apellido Materno')
    primer_nombre = fields.Char(string='Primer Nombre')
    segundo_nombre = fields.Char(string='Segundo Nombre')   
    es_extranjero = fields.Boolean('¿Es Migrante Extranjero?')
    pais_id = fields.Many2one('res.country', string='País', ondelete='restrict')
    celular = fields.Char('Celular')
    operadora_id = fields.Many2one('mz.items', string='Operadora', 
                                  domain=lambda self: [('catalogo_id', '=', self.env.ref('manzana_convoy.catalogo_operadoras').id)])

    # Campos de asistencia y socioeconómicos
    fecha_nacimiento = fields.Date('Fecha de Nacimiento')
    edad = fields.Char(string="Edad", compute="_compute_edad") 
    estado_civil_id = fields.Many2one('mz.items', string='Estado Civil',
                                     domain=lambda self: [('catalogo_id', '=', self.env.ref('manzana_convoy.catalogo_estado_civil').id)])
    genero_id = fields.Many2one('mz.items', string='Género',
                               domain=lambda self: [('catalogo_id', '=', self.env.ref('manzana_convoy.catalogo_genero').id)])
   

    provincia_id = fields.Many2one("res.country.state", string='Provincia', ondelete='restrict', 
                                   domain="[('country_id', '=?', pais_id)]")
    ciudad_id = fields.Many2one('res.country.ciudad', string='Ciudad' , ondelete='restrict', domain="[('state_id', '=?', provincia_id)]")
    
    direccion = fields.Char('Dirección de domicilio')
    email = fields.Char('Correo Electrónico')
    tiene_discapacidad = fields.Boolean('¿Tiene usted alguna discapacidad?')
    recibe_bono = fields.Boolean('¿Recibe algún tipo de bono?')
    tipo_discapacidad_id = fields.Many2one('pf.items', string='Tipo de Discapacidad', 
                                           domain=lambda self: [('catalogo_id', '=', self.env.ref('prefectura_base.tipos_discapacidad').id)])
    nivel_instruccion_id = fields.Many2one('pf.items', string='Nivel de Instrucción',
                                           domain=lambda self: [('catalogo_id', '=', self.env.ref('prefectura_base.catalogo_nivel_instruccion').id)])
    situacion_laboral_id = fields.Many2one('pf.items', string='Situación Laboral',
                                           domain=lambda self: [('catalogo_id', '=', self.env.ref('prefectura_base.catalogo_situacion_laboral').id)])
    tipo_vivienda_id = fields.Many2one('pf.items', string='La vivienda donde habita es?', 
                                       domain=lambda self: [('catalogo_id', '=', self.env.ref('prefectura_base.catalogo_tipo_vivienda').id)])
     
    # Campos de servicios básicos
    tiene_internet = fields.Selection([('si', 'SI'), ('no', 'NO')], string='¿Su hogar cuenta con internet?')
    tiene_agua_potable = fields.Selection([('si', 'SI'), ('no', 'NO')], string='¿La vivienda donde habita tiene servicio de agua potable por tubería?')
    tiene_luz_electrica = fields.Selection([('si', 'SI'), ('no', 'NO')], string='¿La vivienda donde habita cuenta con luz eléctrica?')
    tiene_alcantarillado = fields.Selection([('si', 'SI'), ('no', 'NO')], string='¿La vivienda donde habita tiene servicio de alcantarillado?')
    
    # Campos socioeconómicos adicionales
    es_cuidador = fields.Selection([('si', 'SI'), ('no', 'NO')], string='¿Es cuidador/a?')
    hora_tarea_domestica = fields.Integer(string='Horas a tareas domésticas')
    sostiene_hogar = fields.Selection([('si', 'SI'), ('no', 'NO')], string='¿Usted sostiene económicamente su hogar?')
    enfermedad_catastrofica = fields.Selection([('si', 'SI'), ('no', 'NO')], string='¿Padece alguna enfermedad catastrófica?')
    
    # Campos de composición familiar
    hombres_hogar = fields.Integer(string='¿Cuántos hombres viven en el hogar(contando niños)?')
    mujer_hogar = fields.Integer(string='¿Cuántos mujeres viven en el hogar(contando niñas)?')
    ninos_menores = fields.Integer(string='¿Cuántos niños menores de edad habitan en el hogar?')
    ninos_5_estudiando = fields.Integer(string='¿Cuántos niños mayores de 5 años que habitan en el hogar estan estudiando?')
    mujeres_embarazadas = fields.Integer(string='¿Cuántas mujeres embarazadas habitan en su hogar?', default=0)
    mujeres_embarazadas_chequeos = fields.Integer(string='¿Cuántas mujeres embarazadas que habitan en el hogar asisten a chequeos médicos?', default=0)
    mujeres_embarazadas_menores = fields.Integer(string='¿Cuántas de las mujeres embarazadas son menores de 18 años?', default=0)
    mayor_65 = fields.Selection([('si', 'SI'), ('no', 'NO')], string='¿Hay mayores de 65 años viviendo en su hogar?')
    discapacidad_hogar = fields.Selection([('si', 'SI'), ('no', 'NO')], string='¿Hay personas con discapacidad viviendo en su hogar?')
    tiene_discapacidad_hogar = fields.Selection([('si', 'SI'), ('no', 'NO')], string='¿Hay personas con discapacidad viviendo en su hogar?', default='no')
    tipo_discapacidad_hogar_id = fields.Many2one('pf.items', string='¿Qué tipo de discapacidad tiene?',
                                                 domain=lambda self: [('catalogo_id', '=', self.env.ref('prefectura_base.tipos_discapacidad').id)])   
 
    servicio_id = fields.Many2one('mz.asignacion.servicio', string='Servicio', domain="[('programa_id', '=', programa_id)]")
    dependientes_ids = fields.One2many('mz_convoy.dependiente_wizard', 'wizard_id', string='Dependientes')

    @api.model
    def default_get(self, fields_list):
        """Sobrescribimos default_get para cargar datos cuando es promoción"""
        res = super().default_get(fields_list)
        
        if self._context.get('promover_registro') and self._context.get('default_numero_documento'):
            beneficiario = self.env['mz.beneficiario'].search([
                ('numero_documento', '=', self._context.get('default_numero_documento'))
            ], limit=1)
            
            if beneficiario:
                valores = self._prepare_valores_promocion(beneficiario)
                res.update(valores)
        
        return res

    def _prepare_valores_promocion(self, beneficiario):
        """Prepara todos los valores del beneficiario para la promoción"""
        valores = {
            'beneficiario_id': beneficiario.id,
            'tipo_documento': beneficiario.tipo_documento,
            'numero_documento': beneficiario.numero_documento,
            'apellido_paterno': beneficiario.apellido_paterno,
            'apellido_materno': beneficiario.apellido_materno,
            'primer_nombre': beneficiario.primer_nombre,
            'segundo_nombre': beneficiario.segundo_nombre,
            'es_extranjero': beneficiario.es_extranjero,
            'pais_id': beneficiario.pais_id.id,
            'celular': beneficiario.celular,
            'operadora_id': beneficiario.operadora_id.id,
        }

        # Cargar campos adicionales si existen
        if hasattr(beneficiario, 'fecha_nacimiento'):
            valores.update({
                'fecha_nacimiento': beneficiario.fecha_nacimiento,
                'estado_civil_id': beneficiario.estado_civil_id.id if beneficiario.estado_civil_id else False,
                'genero_id': beneficiario.genero_id.id if beneficiario.genero_id else False,
                'provincia_id': beneficiario.provincia_id.id if beneficiario.provincia_id else False,
                'ciudad_id': beneficiario.ciudad_id.id if beneficiario.ciudad_id else False,
                'direccion': beneficiario.direccion if hasattr(beneficiario, 'direccion') else False,
                'email': beneficiario.email if hasattr(beneficiario, 'email') else False,
                'tiene_discapacidad': beneficiario.tiene_discapacidad if hasattr(beneficiario, 'tiene_discapacidad') else False,
                'recibe_bono': beneficiario.recibe_bono if hasattr(beneficiario, 'recibe_bono') else False,
            })

        # Cargar campos socioeconómicos si están disponibles y el tipo es socioeconómico
        if self._context.get('default_tipo_registro') == 'socioeconomico':
            campos_socioeconomicos = {
                'nivel_instruccion_id': beneficiario.nivel_instruccion_id.id if beneficiario.nivel_instruccion_id else False,
                'situacion_laboral_id': beneficiario.situacion_laboral_id.id if beneficiario.situacion_laboral_id else False,
                'tipo_vivienda_id': beneficiario.tipo_vivienda_id.id if beneficiario.tipo_vivienda_id else False,
                'tiene_internet': beneficiario.tiene_internet if hasattr(beneficiario, 'tiene_internet') else False,
                'tiene_agua_potable': beneficiario.tiene_agua_potable if hasattr(beneficiario, 'tiene_agua_potable') else False,
                'tiene_luz_electrica': beneficiario.tiene_luz_electrica if hasattr(beneficiario, 'tiene_luz_electrica') else False,
                'tiene_alcantarillado': beneficiario.tiene_alcantarillado if hasattr(beneficiario, 'tiene_alcantarillado') else False,
                'es_cuidador': beneficiario.es_cuidador if hasattr(beneficiario, 'es_cuidador') else False,
                'hora_tarea_domestica': beneficiario.hora_tarea_domestica if hasattr(beneficiario, 'hora_tarea_domestica') else 0,
                'sostiene_hogar': beneficiario.sostiene_hogar if hasattr(beneficiario, 'sostiene_hogar') else False,
                'enfermedad_catastrofica': beneficiario.enfermedad_catastrofica if hasattr(beneficiario, 'enfermedad_catastrofica') else False,
                'hombres_hogar': beneficiario.hombres_hogar if hasattr(beneficiario, 'hombres_hogar') else 0,
                'mujer_hogar': beneficiario.mujer_hogar if hasattr(beneficiario, 'mujer_hogar') else 0,
                'ninos_menores': beneficiario.ninos_menores if hasattr(beneficiario, 'ninos_menores') else 0,
                'ninos_5_estudiando': beneficiario.ninos_5_estudiando if hasattr(beneficiario, 'ninos_5_estudiando') else 0,
                'mujeres_embarazadas': beneficiario.mujeres_embarazadas if hasattr(beneficiario, 'mujeres_embarazadas') else 0,
                'mujeres_embarazadas_chequeos': beneficiario.mujeres_embarazadas_chequeos if hasattr(beneficiario, 'mujeres_embarazadas_chequeos') else 0,
                'mujeres_embarazadas_menores': beneficiario.mujeres_embarazadas_menores if hasattr(beneficiario, 'mujeres_embarazadas_menores') else 0,
                'mayor_65': beneficiario.mayor_65 if hasattr(beneficiario, 'mayor_65') else False,
                'tiene_discapacidad_hogar': beneficiario.tiene_discapacidad_hogar if hasattr(beneficiario, 'tiene_discapacidad_hogar') else False,
                'tipo_discapacidad_hogar_id': beneficiario.tipo_discapacidad_hogar_id.id if beneficiario.tipo_discapacidad_hogar_id else False,
            }
            valores.update(campos_socioeconomicos)

        return valores

    
    @api.depends('fecha_nacimiento')
    def _compute_edad(self):
        for record in self:
            if record.fecha_nacimiento:
                hoy = date.today()
                diferencia = relativedelta(hoy, record.fecha_nacimiento)
                record.edad = f"{diferencia.years} años, {diferencia.months} meses, {diferencia.days} días"
            else:
                record.edad = "Sin fecha de nacimiento"

   
#VERIFICAR EL CORRECTO FUNCIONAMIENTO DE ESTA PANTALLA
    @api.onchange('numero_documento')
    def _onchange_tipo_registro(self):               
        if self.numero_documento:
            beneficiario = self.env['mz.beneficiario'].search([
                ('numero_documento', '=', self.numero_documento)
            ], limit=1)             
            self._cargar_beneficiario(beneficiario)
        else:
            self.apellido_paterno = False
            self.apellido_materno = False
            self.primer_nombre = False
            self.segundo_nombre = False
            self.es_extranjero = False
            self.pais_id = False
            self.celular = False
            self.operadora_id = False
            self.fecha_nacimiento = False
            self.estado_civil_id = False
            self.genero_id = False
            self.provincia_id = False
            self.ciudad_id = False
            self.direccion = False
            self.email = False
            self.tiene_discapacidad = False
            self.recibe_bono = False
            self.dependientes_ids = [(5, 0, 0)]  # Limpiar dependientes

            # Limpiar campos socioeconómicos si existen
            if hasattr(self, 'nivel_instruccion_id'):
                self.nivel_instruccion_id = False
                self.situacion_laboral_id = False
                self.tipo_vivienda_id = False
                self.tiene_internet = False
                self.tiene_agua_potable = False
                self.tiene_luz_electrica = False
                self.tiene_alcantarillado = False
                self.es_cuidador = False
                self.hora_tarea_domestica = False
                self.sostiene_hogar = False
                self.enfermedad_catastrofica = False
                self.hombres_hogar = False
                self.mujer_hogar = False
                self.ninos_menores = False
                self.ninos_5_estudiando = False
                self.mujeres_embarazadas = False
                self.mujeres_embarazadas_chequeos = False
                self.mujeres_embarazadas_menores = False
                self.mayor_65 = False
                self.tiene_discapacidad_hogar = False
                self.tipo_discapacidad_hogar_id = False
        
    def _cargar_beneficiario(self, beneficiario):
        """Carga los datos del beneficiario encontrado incluyendo dependientes"""
        # Cargar los datos del beneficiario
        self.beneficiario_id = beneficiario.id       
        self.apellido_paterno = beneficiario.apellido_paterno
        self.apellido_materno = beneficiario.apellido_materno
        self.primer_nombre = beneficiario.primer_nombre
        self.segundo_nombre = beneficiario.segundo_nombre
        self.es_extranjero = beneficiario.es_extranjero
        self.pais_id = beneficiario.pais_id.id
        self.celular = beneficiario.celular
        self.operadora_id = beneficiario.operadora_id.id
        
        # Cargar campos adicionales según el tipo de registro
        if self.tipo_registro in ['asistencia', 'socioeconomico']:
            self._cargar_campos_adicionales(beneficiario)
        
        # Limpiar dependientes existentes
        self.dependientes_ids = [(5, 0, 0)]  # Limpiamos los registros existentes
        
        # Cargar dependientes existentes
        for dependiente in beneficiario.dependientes_ids:
            self.dependientes_ids = [(0, 0, {
                'tipo_dependiente': dependiente.tipo_dependiente.id,
                'primer_apellido': dependiente.primer_apellido,
                'segundo_apellido': dependiente.segundo_apellido,
                'primer_nombre': dependiente.primer_nombre,
                'segundo_nombre': dependiente.segundo_nombre,
                'fecha_nacimiento': dependiente.fecha_nacimiento,
                'tipo_documento': dependiente.tipo_documento,
                'numero_documento': dependiente.numero_documento,
            })]
        

    

    def _cargar_campos_adicionales(self, beneficiario):
        """Carga campos adicionales para registros de asistencia y socioeconómicos"""
        self.fecha_nacimiento = beneficiario.fecha_nacimiento
        self.estado_civil_id = beneficiario.estado_civil_id.id
        self.genero_id = beneficiario.genero_id.id
        self.provincia_id = beneficiario.provincia_id
        self.ciudad_id = beneficiario.ciudad_id
        self.direccion = beneficiario.direccion
        self.email = beneficiario.email        
        self.recibe_bono = beneficiario.recibe_bono
        self.tiene_discapacidad = beneficiario.tiene_discapacidad
        self.tipo_discapacidad_id = beneficiario.tipo_discapacidad_id.id
        
        if self.tipo_registro == 'socioeconomico':
            self.nivel_instruccion_id = beneficiario.nivel_instruccion_id.id
            self.situacion_laboral_id = beneficiario.situacion_laboral_id.id
            self.tipo_vivienda_id = beneficiario.tipo_vivienda_id.id
            self.tiene_internet = beneficiario.tiene_internet
            self.tiene_agua_potable = beneficiario.tiene_agua_potable
            self.tiene_luz_electrica = beneficiario.tiene_luz_electrica
            self.tiene_alcantarillado = beneficiario.tiene_alcantarillado
            self.es_cuidador = beneficiario.es_cuidador
            self.hora_tarea_domestica = beneficiario.hora_tarea_domestica
            self.sostiene_hogar = beneficiario.sostiene_hogar
            self.enfermedad_catastrofica = beneficiario.enfermedad_catastrofica
            self.hombres_hogar = beneficiario.hombres_hogar
            self.mujer_hogar = beneficiario.mujer_hogar
            self.ninos_menores = beneficiario.ninos_menores
            self.ninos_5_estudiando = beneficiario.ninos_5_estudiando
            self.mujeres_embarazadas = beneficiario.mujeres_embarazadas
            self.mujeres_embarazadas_chequeos = beneficiario.mujeres_embarazadas_chequeos
            self.mujeres_embarazadas_menores = beneficiario.mujeres_embarazadas_menores
            self.mayor_65 = beneficiario.mayor_65
            self.tiene_discapacidad_hogar = beneficiario.tiene_discapacidad_hogar
            self.tipo_discapacidad_hogar_id = beneficiario.tipo_discapacidad_hogar_id.id

    def _prepare_beneficiary_values(self):
        """Prepara los valores para crear/actualizar el beneficiario"""
        # Valores base que serán usados tanto para pf.beneficiario como para mz.beneficiario
        vals = {
            'programa_id': self.programa_id.id,
            'tipo_documento': self.tipo_documento,
            'numero_documento': self.numero_documento,
            'apellido_paterno': self.apellido_paterno,
            'apellido_materno': self.apellido_materno,
            'primer_nombre': self.primer_nombre,
            'segundo_nombre': self.segundo_nombre,
            'es_extranjero': self.es_extranjero,
            'pais_id': self.pais_id.id,
            'celular': self.celular,
            'operadora_id': self.operadora_id.id,
        }
        
        if self.tipo_registro in ['asistencia', 'socioeconomico']:
            vals.update({
                'fecha_nacimiento': self.fecha_nacimiento,
                'estado_civil_id': self.estado_civil_id.id,
                'genero_id': self.genero_id.id,
                'provincia_id': self.provincia_id.id,
                'ciudad_id': self.ciudad_id.id,
                'direccion': self.direccion,
                'email': self.email,
                'tiene_discapacidad': self.tiene_discapacidad,
                'recibe_bono': self.recibe_bono,
                'tipo_discapacidad_id': self.tipo_discapacidad_id.id
            })
            
            if self.tipo_registro == 'socioeconomico':
                vals.update({
                    'nivel_instruccion_id': self.nivel_instruccion_id.id,
                    'situacion_laboral_id': self.situacion_laboral_id.id,
                    'tipo_vivienda_id': self.tipo_vivienda_id.id,
                    'tiene_internet': self.tiene_internet,
                    'tiene_agua_potable': self.tiene_agua_potable,
                    'tiene_luz_electrica': self.tiene_luz_electrica,
                    'tiene_alcantarillado': self.tiene_alcantarillado,
                    'es_cuidador': self.es_cuidador,
                    'hora_tarea_domestica': self.hora_tarea_domestica,
                    'sostiene_hogar': self.sostiene_hogar,
                    'enfermedad_catastrofica': self.enfermedad_catastrofica,
                    'hombres_hogar': self.hombres_hogar,
                    'mujer_hogar': self.mujer_hogar,
                    'ninos_menores': self.ninos_menores,
                    'ninos_5_estudiando': self.ninos_5_estudiando,
                    'mujeres_embarazadas': self.mujeres_embarazadas,
                    'mujeres_embarazadas_chequeos': self.mujeres_embarazadas_chequeos,
                    'mujeres_embarazadas_menores': self.mujeres_embarazadas_menores,
                    'mayor_65': self.mayor_65,
                    'tiene_discapacidad_hogar': self.tiene_discapacidad_hogar,
                    'tipo_discapacidad_hogar_id': self.tipo_discapacidad_hogar_id.id if self.tiene_discapacidad_hogar == 'si' else False,
                })
        
        return vals

    def action_register(self):
        """Registra o actualiza el beneficiario en mz.beneficiario y lo añade al convoy.
        También crea o actualiza los dependientes del beneficiario."""
        
        # Preparar los valores para el beneficiario
        vals = self._prepare_beneficiary_values()
        
        # Buscar si existe el beneficiario
        existing_beneficiario = self.env['mz.beneficiario'].search([
            ('numero_documento', '=', self.numero_documento)
        ], limit=1)
        
        if existing_beneficiario:
            # Si existe, actualizamos los campos del beneficiario existente
            existing_beneficiario.write(vals)
            beneficiario = existing_beneficiario
        else:
            # Si no existe, creamos uno nuevo
            beneficiario = self.env['mz.beneficiario'].create(vals)

        # Crear o actualizar la relación convoy-beneficiario
        rel_vals = {
            'convoy_id': self.convoy_id.id,
            'beneficiario_id': beneficiario.id,
            'tipo_registro': self.tipo_registro,
            'fecha_registro': fields.Datetime.now(),
        }
        
        # Agregar servicio si aplica
        if self.tipo_registro in ['asistencia', 'socioeconomico']:
            rel_vals['servicio_id'] = self.servicio_id.id if self.servicio_id else False

        # Verificar si ya existe la relación
        existing_rel = self.env['mz_convoy.beneficiario'].search([
            ('convoy_id', '=', self.convoy_id.id),
            ('beneficiario_id', '=', beneficiario.id)
        ], limit=1)
        
        if existing_rel:
            # Si existe, actualizamos los datos
            existing_rel.write(rel_vals)
        else:
            # Si no existe, creamos la relación
            self.env['mz_convoy.beneficiario'].create(rel_vals)

        # Procesar los dependientes del beneficiario
        for dependiente_wizard in self.dependientes_ids:
            dependiente_vals = {
                'primer_apellido': dependiente_wizard.primer_apellido,
                'segundo_apellido': dependiente_wizard.segundo_apellido,
                'primer_nombre': dependiente_wizard.primer_nombre,
                'segundo_nombre': dependiente_wizard.segundo_nombre,
                'fecha_nacimiento': dependiente_wizard.fecha_nacimiento,
                'tipo_dependiente': dependiente_wizard.tipo_dependiente.id,
                'tipo_documento': dependiente_wizard.tipo_documento,
                'numero_documento': dependiente_wizard.numero_documento,
                'beneficiario_id': beneficiario.id,  # Relacionar el dependiente con el beneficiario
            }
            
            # Buscar si el dependiente ya existe
            existing_dependiente = self.env['mz.dependiente'].search([
                ('numero_documento', '=', dependiente_wizard.numero_documento),
                ('beneficiario_id', '=', beneficiario.id)
            ], limit=1)
            
            if existing_dependiente:
                # Si existe, actualizamos sus datos
                existing_dependiente.write(dependiente_vals)
            else:
                # Si no existe, lo creamos
                self.env['mz.dependiente'].create(dependiente_vals)

        # Recargar la vista para reflejar cambios
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
