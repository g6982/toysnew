# -*- coding: utf-8 -*-
from odoo import fields, models, api, _, SUPERUSER_ID

import logging
_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    is_paid_total_not_efective = fields.Boolean(help='Es pago total que no sea con efectivo', compute='_compute_paid_total_card')

    @api.depends('amount_paid')
    def _compute_paid_total_card(self):
        for record in self:
            # if record.id == 5251:
            #     a = 1
            paid_total_card = False
            c = 0
            if record.amount_paid == record.amount_total:
                if record.payment_ids:
                    payments = record.payment_ids.filtered(lambda x:x.amount > 0)
                    for p in payments:
                        if not p.payment_method_id.is_cash_count:
                            c += 1
                    if c == len(payments.ids): #Verifico si el pago de toda la orden fue con un método que no sea efecgivo
                        paid_total_card = True

            record.is_paid_total_not_efective = paid_total_card




