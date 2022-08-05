# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from datetime import date, datetime

class pos_config(models.Model):
    _inherit = 'pos.config'

    include_tax_in_product = fields.Boolean('Incluir impuestos en el precio del producto')