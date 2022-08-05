# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################

from odoo import api, fields, models, _

class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    is_store_pickup = fields.Boolean(string="Use As Store Pickup")
    store_ids = fields.Many2many('sale.shop', 'carrier_store', 'carrier_id', 'store_ids', string="Choose Store", domain=[('store_active', '=', True)])