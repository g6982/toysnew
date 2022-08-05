# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.tools.float_utils import float_is_zero


class StockWarehouseOrderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    qty_available = fields.Float(string=u'Disponible en Almacén', digits='Product Unit of Measure', compute='_compute_qty_available')

    product_packaging = fields.Many2one('product.packaging',string='Empaquetado', compute='_compute_product_packaging')

    @api.depends('warehouse_id','location_id','product_id','product_tmpl_id')
    def _compute_qty_available(self):
        for record in self:
            qty_available = 0.0
            #locations_internal_ids = record.warehouse_id.lot_stock_id.ids
            location_ids = record.company_id.location_available_id.ids
            if not location_ids:
                location_ids = record.warehouse_id.lot_stock_id.ids
            stock_quant = record.env['stock.quant'].sudo().search([('product_id','=',record.product_id.id),('location_id','in',location_ids)])
            if stock_quant:
                for sq in stock_quant:
                    qty_available += sq.available_quantity
            record.qty_available = qty_available

    @api.depends('product_id', 'product_tmpl_id')
    def _compute_product_packaging(self):
        for record in self:
            product_packaging = False
            if record.product_id:
                if record.product_id.packaging_ids:
                    product_packaging = record.product_id.packaging_ids[0]

            record.product_packaging = product_packaging
