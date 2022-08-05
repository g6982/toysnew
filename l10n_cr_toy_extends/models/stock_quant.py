# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools.float_utils import float_is_zero


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    pending_delivery = fields.Float('A entregar', related='product_id.pending_delivery',digits='Product Unit of Measure',)
    pending_reception = fields.Float('A recibir',  related='product_id.pending_reception',digits='Product Unit of Measure',)




