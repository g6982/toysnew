# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_is_zero, float_compare


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _get_combine_receivable_vals(self, payment_method, amount, amount_converted):
        partial_vals = {
            'account_id': payment_method.receivable_account_id.id,
            'move_id': self.move_id.id,
            'name': '%s - %s' % (self.name, payment_method.name),
            'forma_pago_id': payment_method.id
        }
        return self._debit_amounts(partial_vals, amount, amount_converted)