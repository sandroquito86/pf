from odoo import models, fields, api

class Cie10(models.Model):
    _name = 'pf.cie10'
    _description = 'Clasificación Internacional de Enfermedades (CIE-10)'
    _rec_name = 'display_name'

    code = fields.Char(string='Código', required=True, index=True)
    name = fields.Char(string='Nombre', required=True)
    description = fields.Text(string='Descripción')
    category = fields.Char(string='Categoría')
    parent_id = fields.Many2one('pf.cie10', string='Padre')
    child_ids = fields.One2many('pf.cie10', 'parent_id', string='Subcategorías')

    display_name = fields.Char(string='Nombre completo', compute='_compute_display_name', store=True)

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"[{record.code}] {record.name}"