# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round
from odoo.exceptions import AccessError, UserError, ValidationError

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    metro_cubico = fields.Float(string=u'M^3',  store=True,compute='_computed_metro_cubico')
    note_toys = fields.Text('Nota')

    qty_available = fields.Float(string='Cant.Disponible',digits='Product Unit of Measure',)
    amount_invoiced = fields.Monetary(string='Cant.Facturable', store=True, compute='_compute_amount_invoiced')

    qty_reserved = fields.Float(string='Cant.Reservada',store=True, compute='_compute_qty_reserved',digits='Product Unit of Measure', )

    sale_order_reserved_now = fields.Many2many('sale.order')


    number = fields.Integer(
        compute='_compute_get_number',
        store=True,
    )

    @api.depends('sequence', 'order_id')
    def _compute_get_number(self):
        for order in self.mapped('order_id'):
            number = 1
            for line in order.order_line:
                line.number = number
                number += 1

    @api.depends('qty_available','price_unit')
    def _compute_amount_invoiced(self):
        for record in self:
            record.amount_invoiced = record.qty_available * record.price_unit

    @api.depends('product_id','order_id.partner_id')
    def _compute_qty_reserved(self):
        for record in self:
            array_so = []
            qty_reserved = 0.0

            def _exist_sale_order(o):
                so = self.env['sale.order'].sudo().search([('name','=',o),('partner_id','=', record.order_id.partner_id.id)])
                if so:
                    return so
                else:
                    return False

            def _exist_purchase_order(o):
                po = self.env['purchase.order'].sudo().search([('name', '=', o),('partner_id','=', record.order_id.partner_id.id)])
                if po:
                    return po
                else:
                    return False

            if record.product_id:
                product_uom_qty = 0.0
                stock_move_with_partner = self.env['stock.move'].sudo()
                sale_orders_with_reserved = self.env['sale.order'].sudo()
                stock_moves = self.env['stock.move'].sudo().search([('product_id','=',record.product_id.id),('state','=','assigned')])
                if stock_moves:
                    for sm in stock_moves:
                        origin = sm.origin
                        so = _exist_sale_order(origin)
                        if so:
                            array_so.append(so)
                            sale_orders_with_reserved += so
                            stock_move_with_partner += sm
                        # elif not so:
                        #     po = _exist_purchase_order(origin)
                        #     if po:
                        #         stock_move_with_partner += sm
                        #     else:
                        #         pass
                        else:
                            pass

                if stock_move_with_partner:
                    for smp in stock_move_with_partner:
                        product_uom_qty += smp.product_uom_qty

                record.qty_reserved = product_uom_qty
                record.sale_order_reserved_now = sale_orders_with_reserved


            else:
                record.qty_reserved = qty_reserved

    @api.depends('product_uom_qty', 'product_packaging')
    def _computed_metro_cubico(self):
        self._calc_metro_cubico()

    def _calc_metro_cubico(self):
        for line in self:
            if line.product_id.volume == 0.0 and line.product_packaging:
                raise UserError(
                    _('El producto no tiene un volumen. Por favor, asegúrse de ingresar el campo volumen para calcular los métros cúbicos.'))
            if line.product_id.volume >0.0 and line.product_packaging:
                if line.product_qty%line.product_packaging.qty!=0:
                    raise UserError(
                        _('La cantidad ingresada debe ser múltiplo de la cantidad especificada en el empaquetado !'))
                volume = line.product_id.volume
                qty = line.product_qty
                m3 = volume * qty
                line.metro_cubico = m3

    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        for line in self:
            if line.product_id:
                #ine.product_id._compute_quantities()
                #line._compute_qty_reserved()
                line.qty_available = line.product_id.qty_available
                if line.order_id.discount_partner > 0.0:
                    line.discount = line.order_id.discount_partner

        return res



    def view_qty_reserved(self):

        return {
            'name': _('Órdenes con reserva'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.sale_order_reserved_now.ids)],
        }


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    metro_cubico = fields.Float(string=u'Total M^3',store=True,compute='_computed_metro_cubico', copy=False)

    so_origin_ids = fields.Many2many('sale.order', 'rel_so_somerge_ids','so_id','so_merge_id', string='Ordenes relacionadas', copy=False)
    so_origin_counts = fields.Integer(compute='_compute_sales_related', copy=False)

    confirmation_seller = fields.Boolean('Confirmación para vendedor')
    type_confirm = fields.Selection([('odoo','Odoo'),('seller','Vendedor')], default='seller', string=u'Tipo confirmación')

    carrier_id = fields.Many2one("delivery.carrier", string="Método entrega",)
    carrier_partner_id = fields.Many2one("delivery.carrier", related='partner_id.property_delivery_carrier_id')
    carrier_different_is = fields.Boolean(compute='_compute_carrier_different_is')

    @api.depends('carrier_id','carrier_partner_id','partner_id')
    def _compute_carrier_different_is(self):
        for record in self:
            carrier_different_is = False
            if record.carrier_partner_id or record.carrier_id:
                if record.carrier_partner_id != record.carrier_id:
                    carrier_different_is = True

            record.carrier_different_is = carrier_different_is

    def assign_carrier_different_partner(self):
        for record in self:
            if record.partner_id.property_delivery_carrier_id:
                record.carrier_id = record.partner_id.property_delivery_carrier_id
                record.carrier_different_is = False

    @api.depends('order_line.metro_cubico','order_line.product_uom_qty','order_line.product_packaging')
    def _computed_metro_cubico(self):
        total_metro_cubico = 0.0
        for order in self:
            for line in order.order_line:
                if line.metro_cubico>0.0:
                    total_metro_cubico+=line.metro_cubico

            order.metro_cubico = total_metro_cubico

    @api.constrains('metro_cubico')
    def _check_metro_cubico(self):
        for order in self:
            for line in order.order_line:
                if line.product_id and line.product_packaging:
                    if line.product_qty % line.product_packaging.qty != 0:
                        raise UserError(
                            _('La cantidad ingresada para el producto ' + str(
                                line.product_id.name) + ' no es múltiplo de la cantidad de empaquetado !'))

    discount_partner = fields.Float(string='Descuento', default=0.0)
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super(SaleOrder, self).onchange_partner_id()
        if self.pricelist_id and self.partner_id:
            self.discount_partner = self.partner_id.self.discount_partner

    @api.onchange('discount_partner')
    def _onchange_discount_partner(self):
        for record in self:
            if record.order_line and (record.discount_partner or record.percentage_discount_global):
                for line in record.order_line:
                    disc = record.discount_partner
                    if record.percentage_discount_global and line.discount:
                        record.calc_discount()
                    else:
                        line.discount = disc

    #sobreescritura de l10n_cr_electronic_invoice
    def calc_discount(self):
        for order in self:
            order.re_calcule = False
            if order.apply_discount_global:
                if order.percentage_discount_global >= 0.0:
                    if order.order_line:
                        total = len(order.order_line.ids)
                        percentage_discount = self._percent_discount(order.percentage_discount_global, total)
                        array = []
                        for line in order.order_line:
                            if line.product_id:
                                disc_o = order.discount_partner #descuento original
                                if len(line.ids) > 0:
                                    ids = line.ids[0]
                                else:
                                    ids = line.id.ref

                                d = percentage_discount + disc_o

                                array.append((1, ids, {'discount': d}))
                        if len(array) > 0:
                            order.write({'order_line': array})



    def action_view_sales_related(self):
        if self.so_origin_ids:
            result = {
                'name': _('Órdenes creadas'),
                'type': 'ir.actions.act_window',
                'res_model': 'sale.order',
                'view_mode': 'list',
                'domain': [('id', 'in', self.so_origin_ids.ids)],
                'views': [(self.env.ref('sale.view_quotation_tree').id, 'list'), (self.env.ref('sale.view_order_form').id, 'form')]
            }
            return result
    def _compute_sales_related(self):
        for record in self:
            record.so_origin_counts = len(record.so_origin_ids)
    
    
    def action_confirm(self):
        for record in self:
            if record.company_id.confirmation_seller and not record.confirmation_seller and record.type_confirm == 'seller':
                action = {
                    'name': _('VALIDACIÓN DE LA ORDEN'),
                    'view_mode': 'form',
                    'res_model': 'message.seller.approval.wizard',
                    'view_id': self.env.ref('l10n_cr_toy_extends.message_seller_approval_wizard_form').id,
                    'type': 'ir.actions.act_window',
                    'context': {'default_sale_id': self.id},
                    'target': 'new'
                }

                return action
            else:
                return super(SaleOrder, self).action_confirm()

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super(SaleOrder, self).onchange_partner_id()
        self.carrier_id = self.partner_id.property_delivery_carrier_id
        return res

    @api.depends('picking_ids')
    def _compute_picking_ids(self):
        res = super(SaleOrder, self)._compute_picking_ids()
        for order in self:
            if order.picking_ids:
                for pick in order.picking_ids:
                    pick.carrier_id = order.carrier_id
        return res