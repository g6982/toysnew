# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from datetime import date, datetime


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    is_card = fields.Boolean('Es tarjeta')
    is_transfer = fields.Boolean('Es transferencia')


class PosPayent(models.Model):
    _inherit = 'pos.payment'

    amount_real = fields.Float(string='Monto real')
    is_card = fields.Boolean(related='payment_method_id.is_card', string='Pagado por tarjeta')
    is_transfer = fields.Boolean(related='payment_method_id.is_transfer', string='Pagado por transferencia')


