# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round
from odoo.exceptions import AccessError, UserError, ValidationError

class AccountMove(models.Model):
    _inherit = 'account.move'

    discount_partner = fields.Float(string='Descuento del cliente', default=0.0)



