from odoo import api, fields, models, _
from odoo.tools import formatLang
from odoo.exceptions import ValidationError


class PosPayment(models.Model):
    _inherit = "pos.payment"

    session_id = fields.Many2one('pos.session', string='Sesión', store=True, related=False)

    @api.constrains('payment_method_id')
    def _check_payment_method_id(self):
        for payment in self:
            #if payment.payment_method_id not in payment.session_id.config_id.payment_method_ids:
            if payment.payment_method_id not in payment.pos_order_id.session_id.config_id.payment_method_ids:
                raise ValidationError(_('El método de pago seleccionado no está permitido en la configuración de la sesión de POS.'))