# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class pf/pf_personalizacion(models.Model):
#     _name = 'pf/pf_personalizacion.pf/pf_personalizacion'
#     _description = 'pf/pf_personalizacion.pf/pf_personalizacion'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

