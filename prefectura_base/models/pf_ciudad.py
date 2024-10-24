from odoo import models, fields, api
from odoo.exceptions import ValidationError
from string import ascii_letters, digits
from odoo.osv import expression
from odoo.modules.module import get_module_resource

class CountryState(models.Model):
    _inherit = 'res.country.state'

    city_ids = fields.One2many('res.country.ciudad', 'state_id', string='Ciudades')


class Ciudad(models.Model):
    _name = 'res.country.ciudad'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Ciudad/Cantón'

    name = fields.Char(string='Ciudad',)
    numero_ciudad = fields.Char(string='Número Ciudad',)
    country_id = fields.Many2one('res.country', string='País', ondelete='restrict',)    
    state_id = fields.Many2one(string='Provincia', comodel_name='res.country.state', ondelete='restrict', domain="[('country_id', '=?', country_id)]")   
    parroquia_ids = fields.One2many(string='Parroquias', comodel_name='res.country.parroquia', inverse_name='ciudad_id')

    
    @api.onchange('country_id')
    def _onchange_country_id(self):
        for record in self:
            record.state_id = False
    
    

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None, order='name'):
        args = args or []
        if self.env.context.get('state_id'):
            args = expression.AND([args, [('state_id', '=', self.env.context.get('state_id'))]])

        if operator == 'ilike' and not (name or '').strip():
            first_domain = []
            domain = []
        else:
            first_domain = [('numero_ciudad', '=ilike', name)]
            domain = [('name', operator, name)]

        first_state_ids = self._search(expression.AND([first_domain, args]), limit=limit, access_rights_uid=name_get_uid) if first_domain else []
        return list(first_state_ids) + [
            state_id
            for state_id in self._search(expression.AND([domain, args]),
                                         limit=limit, access_rights_uid=name_get_uid)
            if state_id not in first_state_ids
        ]

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} ({}) ({})".format(record.name, record.state_id.name, record.state_id.country_id.code)))
        return result
    
class Parroquia(models.Model):
    _name = 'res.country.parroquia'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Parroquia'

    name = fields.Char(string='Parroquia',)
    numero_parroquia = fields.Char(string='Número Parroquia',)

    ciudad_id = fields.Many2one(string='Ciudad', comodel_name='res.country.ciudad', ondelete='restrict')

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if self.env.context.get('ciudad_id'):
            args = expression.AND([args, [('ciudad_id', '=', self.env.context.get('ciudad_id'))]])

        if operator == 'ilike' and not (name or '').strip():
            first_domain = []
            domain = []
        else:
            first_domain = [('numero_parroquia', '=ilike', name)]
            domain = [('name', operator, name)]

        first_state_ids = self._search(expression.AND([first_domain, args]), limit=limit, access_rights_uid=name_get_uid) if first_domain else []
        return list(first_state_ids) + [
            ciudad_id
            for ciudad_id in self._search(expression.AND([domain, args]),
                                         limit=limit, access_rights_uid=name_get_uid)
            if ciudad_id not in first_state_ids
        ]

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} ({}) ({}) ({})".format(record.name,record.ciudad_id.name, record.ciudad_id.state_id.name, record.ciudad_id.country_id.code)))
        return result