# -*- coding: utf-8 -*-

import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round
from odoo.tools.float_utils import float_repr
from odoo.tools.misc import format_date
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    price_toys = fields.Float('Precio FOB', default=0.0, digits='Product Price',required=True, help="Precio al que se compra el product")


    @api.onchange('price_toys')
    def _onchange_price_toys(self):
        for record in self:
            if record.price_toys:
                record.price = record.price_toys



TYPE_BATERY = [('AAA','AAA'),('AA','AA')]
class ProductTemplate(models.Model):
    _inherit = "product.template"

    code_supplier = fields.Char(string=u'Código de proveedor')

    weight_net = fields.Float('Peso neto', compute='_compute_weight_net', digits='Stock Weight', inverse='_set_weight_net', store=True)

    age_recomended = fields.Float(string='Edad recomendada')
    type_batery = fields.Selection(TYPE_BATERY, string='Tipo batería')

    volume_ft3 = fields.Float('Volumen', compute='_compute_volume_ft3', inverse='_set_volume_ft3', digits='Volume', store=True)
    volume_uom_name_ft3 = fields.Char(string='Volume unit of measure label', compute='_compute_volume_uom_name_ft3')

    tariff_description = fields.Text(string=u'Descripción arancelaria')

    arancel_lines = fields.One2many('product.tlc.line', 'tmpl_id')

    arancel_code = fields.Char(string='Arancel code')
    arancel_description = fields.Char(string='Arancel description')
    arancel_rate = fields.Float(string='Arancel rate')

    @api.depends('product_variant_ids', 'product_variant_ids.weight_net')
    def _compute_weight_net(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.weight_net = template.product_variant_ids.weight_net
        for template in (self - unique_variants):
            template.weight_net = 0.0

    def _set_weight_net(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.weight_net = template.weight_net

    @api.depends('product_variant_ids', 'product_variant_ids.volume')
    def _compute_volume_ft3(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.volume_ft3 = template.product_variant_ids.volume_ft3
        for template in (self - unique_variants):
            template.volume_ft3 = 0.0

    def _set_volume_ft3(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.volume_ft3 = template.volume_ft3

    def _compute_volume_uom_name_ft3(self):
        self.volume_uom_name_ft3 = self._get_volume_uom_name_from_ir_config_parameter_ft3()

    @api.model
    def _get_volume_uom_name_from_ir_config_parameter_ft3(self):
        return self._get_volume_uom_id_from_ir_config_parameter_ft3().display_name

    @api.model
    def _get_volume_uom_id_from_ir_config_parameter_ft3(self):
        return self.env.ref('uom.product_uom_cubic_foot')

    def _get_warehouse_available(self):
        for record in self:
            names = []
            stock_quants = record.env['stock.quant'].search([('product_tmpl_id', '=', record.id), ('quantity', '>', 0), ('location_id.usage', '=', 'internal')])
            if stock_quants:
                location_ids = stock_quants.mapped('location_id')
                warehouses = location_ids.get_warehouse()
                if warehouses:
                    names = warehouses.mapped('name')

            return names

    # @api.onchange('arancel_lines')
    # def _onchange_arancel_lines(self):
    #     for record in self:
    #         if record.product_variant_ids:
    #             for product in record.product_variant_ids:
    #                 if record.arancel_lines:
    #                     product.arancel_lines.unlink()
    #                     product.arancel_lines = record.arancel_lines


class ProductProduct(models.Model):
    _inherit = "product.product"

    weight_net = fields.Float('Peso neto', digits='Stock Weight')
    volume_ft3 = fields.Float('Volumen ', digits='Volume')

    pending_delivery = fields.Float('A entregar', compute='_compute_quantities_toys')
    pending_reception = fields.Float('A recibir', compute='_compute_quantities_toys')

    #arancel_lines = fields.One2many('product.arancel.line', 'product_id')

    @api.depends('stock_move_ids.product_qty', 'stock_move_ids.state')
    @api.depends_context(
        'lot_id', 'owner_id', 'package_id', 'from_date', 'to_date',
        'location', 'warehouse',
    )
    def _compute_quantities_toys(self):
        products = self.filtered(lambda p: p.type != 'service')
        Move = self.env['stock.move'].with_context(active_test=False)
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = self._get_domain_locations()
        domain_move_in = [('product_id', 'in', self.ids)] + domain_move_in_loc
        domain_move_out = [('product_id', 'in', self.ids)] + domain_move_out_loc
        domain_move_in_todo = [('state', 'in', ('draft', 'waiting', 'confirmed'))] + domain_move_in
        domain_move_out_todo = [('state', 'in', ('draft','waiting', 'confirmed'))] + domain_move_out
        moves_in_res = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_in_todo, ['product_id', 'product_qty'], ['product_id'], orderby='id'))
        moves_out_res = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_out_todo, ['product_id', 'product_qty'], ['product_id'], orderby='id'))

        res = dict()
        for product in self.with_context(prefetch_fields=False):
            product_id = product.id
            if not product_id:
                res[product_id] = dict.fromkeys(
                    ['qty_available', 'free_qty', 'incoming_qty', 'outgoing_qty', 'virtual_available'],
                    0.0,
                )
                continue
            rounding = product.uom_id.rounding
            res[product_id] = {}

            if product.default_code == 'MTC4982':
                a=1
            product.pending_reception = float_round(moves_in_res.get(product_id, 0.0), precision_rounding=rounding)
            product.pending_delivery = float_round(moves_out_res.get(product_id, 0.0), precision_rounding=rounding)
            a=1

    # @api.onchange('arancel_lines')
    # def _onchange_arancel_lines(self):
    #     for record in self:
    #         if record.product_tmpl_id:
    #             product_tmpl_id = record.product_tmpl_id
    #             product_tmpl_id.arancel_lines.unlink()
    #             product_tmpl_id.arancel_lines = record.arancel_lines