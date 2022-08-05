# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class PosPayment(models.Model):
    _inherit = 'pos.payment'

    def update_pos_payment_from_pos(self, new_payment_method):
        if new_payment_method:
            self.write({'payment_method_id': new_payment_method})
            return {'status':200, 'message':'Cambio realizado exitosamente!', 'value': ''}
        else:
            return {'status':203, 'message':'Lo sentimos. No se pudo realizar el cambio', 'value': self.payment_method_id.id}

        a = new_payment_method
        b = 1