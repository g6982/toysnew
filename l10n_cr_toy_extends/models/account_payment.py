# coding: utf-8

import datetime

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    sale_order_ids = fields.Many2many('sale.order', string='Órdenes de venta')
    purchase_order_ids = fields.Many2many('purchase.order', string='Órdenes de compra')
