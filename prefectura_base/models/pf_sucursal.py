from odoo import models, fields, api
import re

class Sucursal(models.Model):
    _name = 'pf.sucursal'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Sucursal'

    name = fields.Char(string='Nombre', required=True)
    company_id = fields.Many2one('res.company', string='Compañía', required=True, default=lambda self: self.env.company)
    street = fields.Char(string='Calle')
    street2 = fields.Char(string='Calle 2')
    zip = fields.Char(string='Código Postal')
    pais_id = fields.Many2one('res.country', string='Pais', ondelete='restrict')
    provincia_id = fields.Many2one("res.country.state", string='Provincia', ondelete='restrict', 
                                   domain="[('country_id', '=?', pais_id)]")
    ciudad_id = fields.Many2one('res.country.ciudad', string='Ciudad' , ondelete='restrict', 
                                   domain="[('state_id', '=?', provincia_id)]")
    email = fields.Char(string='Email')
    phone = fields.Char(string='Teléfono')
    mobile = fields.Char(string='Móvil')
    website = fields.Char(string='Sitio Web')
    
    image = fields.Binary(string='Imagen', attachment=True)
    
    active = fields.Boolean(default=True, string='Activo')
    modulo_ids = fields.Many2many(
        'pf.modulo', 
        string="Módulos",
        help="Selecciona los módulos a los que pertenece este beneficiario"
    )
    programas_ids = fields.One2many(
        'pf.programas',
        'sucursal_id',
        string='Programas'
    )

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
    
    @api.model
    def create(self, vals):
        # Aquí puedes agregar lógica adicional antes de crear la sucursal
        return super(Sucursal, self).create(vals)
    
    def write(self, vals):
        # Aquí puedes agregar lógica adicional antes de actualizar la sucursal
        return super(Sucursal, self).write(vals)
    
class PfProgramas(models.Model):
    _name = 'pf.programas'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Programas'

    
    name = fields.Char(string='Nombre', required=True)
    sucursal_id = fields.Many2one('pf.sucursal', string='Sucursal', required=True)
    email = fields.Char(string='Email')
    phone = fields.Char(string='Teléfono')
    mobile = fields.Char(string='Móvil')
    tipo_documento = fields.Many2one('pf.items', string='Tipo de Documento')
    domain_tipo_documento = fields.Char(string='Domain Tipo de Documento',compute='_compute_domain_tipo_documento')
    numero_documento = fields.Char(string='Número de Documento')
    fecha_documento = fields.Date(string='Fecha de Documento')
    file = fields.Binary(string='Archivo', attachment=True)
    name_file = fields.Char(string='Nombre de Archivo')
    provincia_id = fields.Many2one("res.country.state", string='Provincia', ondelete='restrict', related= "sucursal_id.provincia_id")
    ciudad_id = fields.Many2one('res.country.ciudad', string='Ciudad' , ondelete='restrict', related="sucursal_id.ciudad_id")
    street = fields.Char(string='Calle',  related='sucursal_id.street')
    street2 = fields.Char(string='Calle 2', related='sucursal_id.street2')
    zip = fields.Char(string='Código Postal', related='sucursal_id.zip')
    if_publicado = fields.Boolean(string='Publicado', default=False)
    
    
    image = fields.Binary(string='Imagen', attachment=True)
    
    active = fields.Boolean(default=True, string='Activo')
    modulo_id = fields.Many2one(
        'pf.modulo', 
        string="Proceso",
        help="Selecciona el Programa al que pertenece"
    )
    autoridades_ids = fields.Many2many(
        'hr.employee',
        string='Autoridades',
        domain="[('if_autoridad', '=', True)]"
    )
    
    image_128 = fields.Image(string='Imagen', max_width=128, max_height=128)

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
    
