from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date
from dateutil.relativedelta import relativedelta

class Servicio(models.Model):
    _name = 'mz.servicio'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Servicio'

    @api.model
    def _get_tipo_servicio_domain(self):
        catalogo_id = self.env.ref('prefectura_base.tipo_servicio').id
        return [('catalogo_id', '=', catalogo_id)]

    name = fields.Char(string='Nombre', required=True)
    descripcion = fields.Text(string='Descripción')
    active = fields.Boolean(default=True, string='Activo')
    if_derivacion = fields.Boolean(default=False, string='Derivación')
    image = fields.Binary(string='Imagen', attachment=True)
    tipo_servicio = fields.Selection([('normal', 'Bienestar Personal'), ('medico', 'Salud'), ('cuidado_infantil', 'Cuidado Infantil'), ('mascota', 'Mascota'), ('asesoria_legal', 'Asesoria Legal')], string='Clasificación de Servicio', default='normal')
    if_consulta_medica = fields.Boolean(string='Consulta Médica')
    if_consulta_psicologica = fields.Boolean(string='Consulta Psicológica')
    catalogo_tipo_servicio_id = fields.Many2one('pf.items', string='Tipo de Servicio',  domain=_get_tipo_servicio_domain)
    sub_servicio_ids = fields.One2many('mz.sub.servicio', 'servicio_id', string='Sub Servicios')
    active = fields.Boolean(default=True, string='Activo', tracking=True)
    has_been_used = fields.Boolean(
        string='Ha sido utilizado',
        compute='_compute_has_been_used',
        store=True
    )

    _sql_constraints = [('name_unique', 'UNIQUE(name)', "El servicio debe ser único"),]    
    
    @api.constrains('name')
    def _check_name_servicio(self):
        for record in self:
            model_ids = record.search([('id', '!=',record.id)])        
            list_names = [x.name.upper() for x in model_ids if x.name]        
            if record.name.upper() in list_names:
                raise UserError("Ya existe el servicio: %s , no se permiten valores duplicados" % (record.name.upper()))  

    @api.depends()
    def _compute_has_been_used(self):
        for record in self:
            # Buscar si el sub-servicio ha sido usado en agendamientos
            used_in_agendar = self.env['mz.asignacion.servicio'].search_count([
                ('servicio_id', '=', record.id)
            ]) > 0
            
            # Puedes agregar más condiciones según tus necesidades
            record.has_been_used = used_in_agendar

    def unlink(self):
        if any(record.has_been_used for record in self):
            raise UserError('No se pueden eliminar Servicio que ya han sido utilizados. En su lugar, desactívelos(Archivar).')
        return super().unlink()  
 

        
class SubServicio(models.Model):
    _name = 'mz.sub.servicio'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Sub Servicio'

    name = fields.Char(string='Nombre', required=True)
    descripcion = fields.Text(string='Descripción')
    servicio_id = fields.Many2one('mz.servicio', string='Servicio', required=True, ondelete='cascade')
    active = fields.Boolean(default=True, string='Activo')  
    active = fields.Boolean(default=True, string='Activo', tracking=True)
    has_been_used = fields.Boolean(
        string='Ha sido utilizado',
        compute='_compute_has_been_used',
        store=True
    )

    _sql_constraints = [('name_unique', 'UNIQUE(servicio_id,name)', "El subservicio debe ser único en cada servicio"),]    
    
    @api.constrains('name')
    def _check_name_sub_servicio(self):
        for record in self:
            model_ids = record.search([('id', '!=',record.id),('servicio_id', '=',record.servicio_id.id)])        
            list_names = [x.name.upper() for x in model_ids if x.name]        
            if record.name.upper() in list_names:
                raise UserError("Ya existe el subservicio: %s , no se permiten valores duplicados dentro del mismo servicio" % (record.name.upper()))    

    @api.depends()
    def _compute_has_been_used(self):
        for record in self:
            # Buscar si el sub-servicio ha sido usado en agendamientos
            used_in_agendar = self.env['mz.agendar_servicio'].search_count([
                ('sub_servicio_id', '=', record.id)
            ]) > 0
            
            # Puedes agregar más condiciones según tus necesidades
            record.has_been_used = used_in_agendar

    def unlink(self):
        if any(record.has_been_used for record in self):
            raise UserError('No se pueden eliminar sub-servicios que ya han sido utilizados. En su lugar, desactívelos(Archivar).')
        return super().unlink()