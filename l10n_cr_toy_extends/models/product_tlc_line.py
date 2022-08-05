# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round
from odoo.exceptions import AccessError, UserError, ValidationError

class ProductTlcLine(models.Model):
    _name = 'product.tlc.line'
    _inherit = ['mail.thread']
    _description = "Tratado de libre comercio"
    _order = 'sequence desc'

    sequence = fields.Integer(default=10)
    code = fields.Char(string='Código')
    country_id = fields.Many2one('res.country', string='País', required=True)
    description = fields.Char(string='Descripción')
    rate = fields.Float(string='Tasa', required=True)
    tmpl_id = fields.Many2one('product.template', string='Plantilla de producto')
    product_id = fields.Many2one('product.product', string='Producto')
