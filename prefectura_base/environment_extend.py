from odoo import api, SUPERUSER_ID

class Environment(api.Environment):
    @property
    def programa_id(self):
        return self.user.programa_id.id if self.user.programa_id else False

api.Environment = Environment