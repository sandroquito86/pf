from odoo import models, api
from odoo.http import request

class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        result = super(IrHttp, self).session_info()
        user = request.env.user
        if user.programa_id:
            result['user_context']['programa_id'] = user.programa_id.id
        return result