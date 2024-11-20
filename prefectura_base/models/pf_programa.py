from odoo import models, fields, api
import re
    
class PfProgramas(models.Model):
    _name = 'pf.programas'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Programas'

    
    name = fields.Char(string='Nombre', required=True, tracking=True)    
    sigla = fields.Char(string='Abreviatura', required=True, size=10, tracking=True)    
    sucursal_id = fields.Many2one('pf.sucursal', string='Sucursal', required=True, tracking=True)
    email = fields.Char(string='Email', required=True, tracking=True)
    phone = fields.Char(string='Teléfono', tracking=True)
    mobile = fields.Char(string='Móvil', tracking=True)
    tipo_documento = fields.Many2one('pf.items', string='Tipo de Documento' , tracking=True)
    domain_tipo_documento = fields.Char(string='Domain Tipo de Documento',compute='_compute_domain_tipo_documento')
    numero_documento = fields.Char(string='Número de Documento', tracking=True)
    fecha_documento = fields.Date(string='Fecha de Documento')
    file = fields.Binary(string='Archivo', attachment=True, tracking=True)
    name_file = fields.Char(string='Nombre de Archivo', tracking=True)
    provincia_id = fields.Many2one("res.country.state", string='Provincia', ondelete='restrict', related= "sucursal_id.provincia_id", tracking=True)
    ciudad_id = fields.Many2one('res.country.ciudad', string='Ciudad' , ondelete='restrict', related="sucursal_id.ciudad_id", tracking=True)
    street = fields.Char(string='Calle',  related='sucursal_id.street', tracking=True)
    street2 = fields.Char(string='Calle 2', related='sucursal_id.street2', tracking=True)
    zip = fields.Char(string='Código Postal', related='sucursal_id.zip', tracking=True)
    if_publicado = fields.Boolean(string='Publicado', default=False)
    normativa_texto = fields.Html(string='Normativa', help="Descripción detallada de la normativa aplicable a este programa o sucursal.", tracking=True)
    
    image = fields.Binary(string='Imagen', attachment=True)
    
    active = fields.Boolean(default=True, string='Activo', tracking=True)
    modulo_id = fields.Many2one(
        'pf.modulo', 
        string="Proceso",
        help="Selecciona el Programa al que pertenece"
    )
    autoridades_ids = fields.Many2many(
        'hr.employee',
        string='Autoridades',
        # domain="[('if_autoridad', '=', True)]"
    )
    domain_autoridades_ids = fields.Char(string='Domain Autoridades',compute='_compute_autoridades_ids')
    
    image_128 = fields.Image(string='Imagen', max_width=128, max_height=128)

    @api.depends('modulo_id')
    def _compute_autoridades_ids(self):
        for record in self:
            if record.modulo_id:
                employees = self.env['hr.employee'].search([('modulo_ids', 'in', [self.modulo_id.id]), ('if_autoridad', '=', True)])
                record.domain_autoridades_ids = [('id', 'in', employees.ids)]
            else:
                record.domain_autoridades_ids = [('id', 'in', [])]

    @api.depends('sucursal_id')
    def _compute_domain_tipo_documento(self):
        for record in self:
            tipo_documento = self.env['pf.items'].search([('catalogo_id', '=', self.env.ref('prefectura_base.tipo_documentos').id)])
            if tipo_documento:
                record.domain_tipo_documento = [('id', 'in', tipo_documento.ids)]
            else:
                record.domain_tipo_documento = [('id', 'in', [])]

    @api.onchange('email')
    def _onchange_email(self):
        """
        Validate the email format.
        """
        if self.email and not self._validar_email(self.email):
            return {
                'warning': {
                    'title': "Correo Electrónico Inválido",
                    'message': "El correo electrónico ingresado no es válido."
                }
            }
        
    def _validar_email(self, email):
        """
        Validate the email format using a regular expression.
        """
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_regex, email) is not None
    
    @api.onchange('sucursal_id')
    def _onchange_sucursal_id(self):
        if self.env.context.get('default_modulo_id'):
            self.modulo_id = self.env.context['default_modulo_id']

    

    @api.model
    def create(self, vals):
        if 'file' in vals and 'name_file' not in vals:
            vals['name_file'] = self._context.get('default_name_file', 'default_filename')
        return super(PfProgramas, self).create(vals)

    def write(self, vals):
        if 'file' in vals and 'name_file' not in vals:
            vals['name_file'] = self._context.get('default_name_file', 'default_filename')
        return super(PfProgramas, self).write(vals)
    
    
    
    
    
    @api.model
    def create(self, vals):
        # Aquí puedes agregar lógica adicional antes de crear la sucursal
        return super(PfProgramas, self).create(vals)
    
    def write(self, vals):
        # Aquí puedes agregar lógica adicional antes de actualizar la sucursal
        return super(PfProgramas, self).write(vals)
    
