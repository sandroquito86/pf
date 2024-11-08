from odoo import models, fields, api
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError


class Beneficiario(models.Model):
    _name = 'mz_convoy.beneficiario'
    _description = 'Catálogo de Beneficiarios'

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

    @api.onchange('mujeres_embarazadas', 'mujeres_embarazadas_chequeos', 'mujeres_embarazadas_menores')
    def _onchange_field(self):
        for record in self:            
            if record.mujeres_embarazadas_chequeos > record.mujeres_embarazadas:
                raise UserError('El número de mujeres embarazadas que asisten a chequeos no puede ser mayor al número total de mujeres embarazadas.')            
            if record.mujeres_embarazadas_menores > record.mujeres_embarazadas:
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

    _sql_constraints = [
        ('num_documento_uniq', 
         'UNIQUE(num_documento)',
         'Ya existe un beneficiario con este número de documento.')
    ]
