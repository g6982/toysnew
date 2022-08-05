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

from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
# import logging
# _logger = logging.getLogger(__name__)


class WebsiteSale(WebsiteSale):

    def pickup_check_transaction(self):
        transaction_obj = request.env['payment.transaction']
        order = request.website.sale_get_order()
        if order and order.transaction_ids:
            tx = order.transaction_ids[0]
            tx_id = tx.id
            if tx.sale_order_id.id != order.id or tx.state in ['error', 'cancel']:
                tx_id = False
            request.session['sale_transaction_id'] = tx_id
        else:
            request.session['sale_transaction_id'] = False
            return request.redirect("/shop/checkout")

    @http.route(['/shop/payment'], type='http', auth="public", website=True)
    def payment(self, **post):
        self.pickup_check_transaction()
        vals = super(WebsiteSale, self).payment(**post)
        selected_store, max_lead_hours, store_objs, max_lead_time, is_shop = None, None, None, None, 'other'
        order = request.website.sale_get_order()
        if not order.old_warehouse_id:
            temp = order.warehouse_id
            order.sudo().write({'old_warehouse_id': temp.id})

        if order and order.carrier_id:
            if order.carrier_id.sudo().is_store_pickup:
                store_objs = order.carrier_id.sudo().store_ids
                if order.shop_id and order.shop_id in store_objs:
                    selected_store = order.shop_id
                    is_shop = 'yes'
                else:
                    is_shop = 'not'

                max_lead_time = order.customer_lead_time
                if max_lead_time:
                    p_time = float(max_lead_time.rsplit(' ', 1)[0])
                    p_unit = max_lead_time.rsplit(' ', 1)[1]
                    if p_unit == 'hrs':
                        max_lead_hours = p_time
                    elif p_unit == 'days':
                        max_lead_hours = p_time*24
                    elif p_unit == 'weeks':
                        max_lead_hours = p_time*168 #24*7
                    elif p_unit == 'month':
                        max_lead_hours = p_time*720 #24*30
                    elif p_unit == 'years':
                        max_lead_hours = p_time*10950 #24*365
            else:
                temp = order.old_warehouse_id
                order.sudo().write({'shop_id': False, 'warehouse_id': temp.id, 'old_warehouse_id': False})
        vals.qcontext['stores'] = store_objs
        vals.qcontext['is_shop'] = is_shop
        vals.qcontext['selected_store'] = selected_store
        vals.qcontext['max_lead_time'] = max_lead_time
        vals.qcontext['max_lead_hours'] = max_lead_hours
        vals.qcontext['carrier_value'] = order.carrier_id
        return vals

    @http.route(['/store/pickup/json'], type='json', auth="public", website=True)
    def store_pickup_map_json(self, carrier_id=None, **kw):
        if carrier_id:
            selected_store, max_lead_hours, store_objs, max_lead_time, is_shop, values = None, None, None, None, 'other', {}
            DeliveryCarrier = request.env['delivery.carrier']
            order = request.website.sale_get_order()

            Carrier_Obj = DeliveryCarrier.browse(int(carrier_id))

            if not order.old_warehouse_id:
                temp = order.warehouse_id
                order.sudo().write({'old_warehouse_id': temp.id})

            if Carrier_Obj.sudo().is_store_pickup:
                store_objs = Carrier_Obj.sudo().store_ids
                if order.shop_id and order.shop_id in store_objs:
                    selected_store = order.shop_id
                    is_shop = 'yes'
                else:
                    is_shop = 'not'

                max_lead_time = order.customer_lead_time
                if max_lead_time:
                    p_time = float(max_lead_time.rsplit(' ', 1)[0])
                    p_unit = max_lead_time.rsplit(' ', 1)[1]
                    if p_unit == 'hrs':
                        max_lead_hours = p_time
                    elif p_unit == 'days':
                        max_lead_hours = p_time*24
                    elif p_unit == 'weeks':
                        max_lead_hours = p_time*168 #24*7
                    elif p_unit == 'month':
                        max_lead_hours = p_time*720 #24*30
                    elif p_unit == 'years':
                        max_lead_hours = p_time*10950 #24*365
            else:
                temp = order.old_warehouse_id
                order.sudo().write({'shop_id': False, 'warehouse_id': temp.id, 'old_warehouse_id': False})
            values = {
                'stores': store_objs,
                'is_shop': is_shop,
                'selected_store': selected_store,
                'max_lead_time': max_lead_time,
                'max_lead_hours': max_lead_hours,
                'carrier_value': Carrier_Obj,
            }
            return request.env['ir.ui.view']._render_template("website_store_pickup.store_pickup_payment_json",values)
        return False

    @http.route(['/store/pickup/addr'], type='json', auth="public", website=True)
    def store_pickup_addr(self, store_id, **post):
        if store_id:
            max_lead_time, max_lead_hours = None, None
            order = request.website.sale_get_order()
            config_vals = request.env['sale.shop'].get_store_pick_default_value()
            customer_lead_time = config_vals.get('customer_lead_time')
            res = self.check_store_pickup_conditions(store_id, config_vals, order)
            if res:
                if customer_lead_time == 'product_lead':
                    lead_time = []
                    if order and order.order_line:
                        lines = order.order_line
                        for line in lines:
                            lead_time.append(
                                float(line.product_id.product_tmpl_id.sale_delay))
                    max_lead_time = str(max(lead_time)) + ' days'
                    max_lead_hours = float(max(lead_time)) * 24
                else:
                    max_lead_time = str(res.delivery_lead_time) + \
                        ' ' + str(res.lead_time_unit)
                    if res.lead_time_unit == 'hrs':
                        max_lead_hours = int(res.delivery_lead_time)
                    elif res.lead_time_unit == 'days':
                        max_lead_hours = int(res.delivery_lead_time)*24
                    elif res.lead_time_unit == 'weeks':
                        max_lead_hours = int(res.delivery_lead_time)*168 # 24*7
                    elif res.lead_time_unit == 'month':
                        max_lead_hours = int(res.delivery_lead_time)*720 #24*30
                    elif res.lead_time_unit == 'years':
                        max_lead_hours = int(res.delivery_lead_time)*10950 #24*365

                order.sudo().write({'customer_lead_time': max_lead_time})
                return request.env['ir.ui.view']._render_template("website_store_pickup.store_pickup_payment_json",{
                    'store': res,
                    'max_lead_time': max_lead_time,
                    'max_lead_hours': max_lead_hours
                })

            else:
                return False

    def check_store_pickup_conditions(self, store_id, config_vals, order):
        store_obj = request.env['sale.shop'].sudo().browse(int(store_id))
        stock_location_id = store_obj.store_warehouse.lot_stock_id.id
        qty_type = config_vals.get('qty_type')
        order_premission = config_vals.get('order_premission')
        product_qty = config_vals.get('product_qty')
        if order and order.order_line and order.carrier_id and order.carrier_id.sudo().is_store_pickup:
            if order_premission == 'all':
                order.write(
                    {'shop_id': int(store_id), 'warehouse_id': store_obj.store_warehouse.id})
                return store_obj

            lines = order.order_line
            for line in lines:
                if line.product_id.id != order.carrier_id.sudo().product_id.id:
                    context = {}
                    context.update({'states': ('done',), 'what': (
                        'in', 'out'), 'location': int(stock_location_id)})
                    qty = line.product_id.with_context(context).sudo()._product_available()
                    if qty_type == 'on_hand':
                        quantity = qty[line.product_id.id]['qty_available']
                    elif qty_type == 'forecasted':
                        quantity = qty[line.product_id.id]['virtual_available']

                    if (order_premission == 'condition' and quantity < product_qty):
                        break
            else:
                order.write(
                    {'shop_id': int(store_id), 'warehouse_id': store_obj.store_warehouse.id})
                return store_obj
        return False
