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


class SaleShop(models.Model):
    _inherit = 'sale.shop'

    @api.model
    def _default_warehouse_id(self):
        company = self.env.user.company_id.id
        warehouse_id = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
        return warehouse_id

    delivery_lead_time = fields.Float(string="Pickup Lead Time", required=True, default="3.0")
    store_warehouse = fields.Many2one('stock.warehouse', string="Store Warehouse", default=_default_warehouse_id)

    lead_time_unit = fields.Selection([('hrs', 'Hours'),
                                       ('days', 'Days'),
                                       ('weeks', 'Weeks'),
                                       ('month', 'Months'),
                                       ('years', 'Years')
                                       ], string="Lead Time Unit", default="days")

    @api.model
    def get_store_pick_default_value(self):
        """ this function retrn all configuration value for website Preorder module."""
        res = {}
        store_pick_config_values = self.env['website.store.pickup.settings'].sudo().search([('is_active', '=', True)], limit=1)
        if store_pick_config_values:
            res = {
                'customer_lead_time': store_pick_config_values.customer_lead_time,
                'order_premission': store_pick_config_values.order_premission,
                'qty_type': store_pick_config_values.qty_type,
                'product_qty': store_pick_config_values.product_qty,
            }
        return res


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def _default_warehouse_id(self):
        company = self.env.user.company_id.id
        warehouse_ids = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
        return warehouse_ids

    old_warehouse_id = fields.Many2one('stock.warehouse', string='Old Warehouse', default=_default_warehouse_id)
    customer_lead_time = fields.Char(string="Pickup Lead Time")
