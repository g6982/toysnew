# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from odoo.exceptions import AccessError, UserError, ValidationError
from itertools import groupby
from odoo.tools.float_utils import float_is_zero

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round
from odoo.tools.float_utils import float_repr
from odoo.tools.misc import format_date
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


@api.model
def _lang_get(self):
    return self.env['res.lang'].get_installed()

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    metro_cubico = fields.Float(string=u'Total m³', store=True, compute='_computed_metro_cubico', default=0.0)
    type_container = fields.Many2one('container.type', string='Tipo contenedor')
    #remaining_space = fields.Float(string='Espacio restante', store=True, readonly=True, related='type_container.remaining_space')
    remaining_space = fields.Float(string='Espacio restante', store=True, readonly=True, compute='_compute_remaining_space')
    total_package = fields.Float('Total paquetes', store=True, compute='_compute_total_package', default=0.0)
    show_alert_space_not = fields.Boolean(default=False, compute='_compute_show_alert_space_not')
    follow_ids = fields.One2many('purchase.order.follow', 'purchase_id')
    shipping_mark = fields.Char(string='Marca de envío')

    lang_edit = fields.Many2one('res.lang')
    lang = fields.Selection(_lang_get, string='Language',
                            help="All the emails and documents sent to this contact will be translated in this language.")

    @api.constrains('show_alert_space_not')
    def _check_show_alert_space_not(self):
        for record in self:
            if record.show_alert_space_not:
                raise ValidationError(_('Al parecer ha excedido el total restante del contenedor, verifique la órden de compra.'))

    @api.depends('remaining_space','metro_cubico')
    def _compute_show_alert_space_not(self):
        for record in self:
            show_alert_space_not = False
            if record.type_container:
                #show_alert_space_not = True if record.remaining_space < record.metro_cubico else False
                show_alert_space_not = True if record.remaining_space < 0.0 else False #si no es mayor a 0.0 muestra alerta
            record.show_alert_space_not = show_alert_space_not

    @api.constrains('metro_cubico')
    def _check_metro_cubico(self):
        for order in self:
            for line in order.order_line:
                if line.product_id and line.product_packaging:
                    if line.product_qty % line.product_packaging.qty != 0:
                        raise UserError(
                            _('La cantidad ingresada para el producto ' + str(
                                line.product_id.name) + ' no es múltiplo de la cantidad de empaquetado !'))

    @api.depends('order_line.metro_cubico', 'order_line.product_qty', 'order_line.product_packaging')
    def _computed_metro_cubico(self):
        total_metro_cubico = 0.0
        for order in self:
            for line in order.order_line:
                if line.metro_cubico > 0.0:
                    total_metro_cubico += line.metro_cubico
            order.metro_cubico = total_metro_cubico

    @api.depends('type_container', 'type_container.order_ids', 'type_container.space', 'type_container.remaining_space','metro_cubico')
    def _compute_remaining_space(self):
        remaining_space = 0.0
        for record in self:
            if record.type_container:
                if record.type_container.order_ids:
                    if len(record.ids)>0:
                        orders_valid = record.type_container.order_ids.filtered(lambda o: o.state != 'cancel' and o.id != record.ids[0])
                    else:
                        orders_valid = record.type_container.order_ids.filtered(lambda o: o.state != 'cancel')
                    if orders_valid:
                        total = sum(r.metro_cubico for r in orders_valid)
                        remaining_space = record.type_container.space - total
                    else:
                        remaining_space = record.type_container.space
                remaining_space = remaining_space - record.metro_cubico

            record.remaining_space = remaining_space



    @api.depends('order_line.package_qty_in')
    def _compute_total_package(self):
        for record in self:
            record.total_package = sum(l.package_qty_in for l in record.order_line)

    # @api.onchange('type_container')
    # def _onchange_type_container(self):
    #     for record in self:
    #         if record.type_container:
    #             record.remaining_space = record.type_container.remaining_space

    @api.onchange('partner_id', 'company_id')
    def onchange_partner_id(self):
        res = super(PurchaseOrder, self).onchange_partner_id()
        for rec in self:
            if rec.partner_id:
                rec.lang = rec.partner_id.lang
        return res


    def _eval_product_in_picking_and_landed(self):

        def _find_rate_product(product, purchase_line_id,total):
            amount_tlc = 0.0
            amount_tax = 0.0
            for tax in purchase_line_id.taxes_id:
                amount_tax += (total * (tax.amount / 100))
            if product:
                is_cr = False
                country_id = purchase_line_id.order_id.partner_id.country_id
                if not country_id and product.arancel_rate > 0.0:
                    is_cr = True

                elif country_id.code == 'CR':
                    is_cr = True
                elif country_id.code != 'CR':
                    is_cr = False

                if is_cr:
                    if product.arancel_rate == 0.0 and not product.arancel_code and not product.arancel_description:
                        raise ValidationError(_("Falta datos para arancel en Costa Rica en el producto %s " % (product.name)))
                    amount_tlc = total * (product.arancel_rate / 100)
                else:
                    if not product.arancel_lines:
                        raise ValidationError(_("El producto %s no tiene datos ingresados en el TLC" % (product.name)))
                    sw = 0
                    rate = 0.0
                    for a in product.arancel_lines:
                        if a.country_id.id == country_id.id:
                            rate = a.rate
                            sw = 1
                            break

                    if sw == 0:
                        raise ValidationError(_("El producto %s no tiene datos ingresados en el TLC para el país de %s " % (product.name, country_id.name)))
                    else:
                        amount_tlc = total * (rate / 100)

            return amount_tlc, amount_tax

        array_products = []
        for record in self:
            if record.picking_ids:
                picking_ids = False
                if len(record.picking_ids.ids)==1:
                    picking_ids = "("+ str(record.picking_ids.id) + ")"
                else:
                    picking_ids = tuple(record.picking_ids.ids)
                sql = """
                select * from stock_landed_cost_stock_picking_rel
                where stock_picking_id in {0}
                """.format(picking_ids)
                self.env.cr.execute(sql)
                result = self.env.cr.dictfetchall()
                for r in result:
                    stock_landed_cost_id = r['stock_landed_cost_id']
                    landed_cost = record.env['stock.landed.cost'].sudo().browse(stock_landed_cost_id)
                    if landed_cost:

                #landed_cost = record.env['stock.landed.cost'].sudo().search([('picking_ids', 'in', record.picking_ids.ids)])
                        for picking in record.picking_ids:
                            if picking.move_ids_without_package:
                                for move in picking.move_ids_without_package:
                                    if move.purchase_line_id:
                                        p = landed_cost.valuation_adjustment_lines.mapped('product_id').filtered(lambda p:p.id == move.purchase_line_id.product_id.id)
                                        if move.purchase_line_id.apply_tlc and p:
                                            line_landed = landed_cost.valuation_adjustment_lines.filtered(lambda l: l.product_id.id == move.purchase_line_id.product_id.id)
                                            if line_landed:
                                                value_original = line_landed[0]
                                                amount_total = landed_cost.amount_total
                                                total = value_original.former_cost + amount_total
                                                amount_tlc, amount_tax = _find_rate_product(p, move.purchase_line_id,total)
                                                array_products.append({'product_id': p, 'amount_tlc':amount_tlc, 'amount_tax':amount_tax})

        return array_products



    def create_invoice_to_hacienda(self, change_is=False, rate=False):
        """Create the invoice associated to the PO.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        # 1) Prepare invoice vals and clean-up the section lines
        invoice_vals_list = []
        array_products = []
        for order in self:

            array_products = self._eval_product_in_picking_and_landed()
            if array_products:
                if order.invoice_status != 'to invoice':
                    continue

                order = order.with_company(order.company_id)
                pending_section = None
                # Invoice values.
                invoice_vals = order._prepare_invoice_by_hacienda(change_is)
                # Invoice line values (keep only necessary sections).
                for line in order.order_line:
                    if line.display_type == 'line_section':
                        pending_section = line
                        continue
                    if not float_is_zero(line.qty_to_invoice, precision_digits=precision) and len(array_products) > 0:
                        invoice_vals['invoice_line_ids'] = order._prepare_lines_by_hacienda(array_products)
                invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise UserError(_('There is no invoiceable line. If a product has a control policy based on received quantity, please make sure that a quantity has been received.'))

        # 2) group by (company_id, partner_id, currency_id) for batch creation
        new_invoice_vals_list = []
        for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: (x.get('company_id'), x.get('partner_id'), x.get('currency_id'))):
            origins = set()
            payment_refs = set()
            refs = set()
            ref_invoice_vals = None
            for invoice_vals in invoices:
                if not ref_invoice_vals:
                    ref_invoice_vals = invoice_vals
                else:
                    ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                origins.add(invoice_vals['invoice_origin'])
                payment_refs.add(invoice_vals['payment_reference'])
                refs.add(invoice_vals['ref'])
            ref_invoice_vals.update({
                'ref': ', '.join(refs)[:2000],
                'invoice_origin': ', '.join(origins),
                'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
            })
            new_invoice_vals_list.append(ref_invoice_vals)
        invoice_vals_list = new_invoice_vals_list

        # 3) Create invoices.
        moves = self.env['account.move']
        AccountMove = self.env['account.move'].with_context(default_move_type='in_invoice')
        for vals in invoice_vals_list:
            moves |= AccountMove.with_company(vals['company_id']).create(vals)

        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        moves.filtered(lambda m: m.currency_id.round(m.amount_total) < 0).action_switch_invoice_into_refund_credit_note()

        return self.action_view_invoice(moves)


    def _prepare_lines_by_hacienda(self,array_products):


        amount_tlc = 0.0
        amount_tax = 0.0
        if len(array_products) > 0:
            amount_tlc = sum(x['amount_tlc'] for x in array_products)
            amount_tax = sum(x['amount_tax'] for x in array_products)

        PRODUCTS = [
            {'product': self.env.ref('l10n_cr_toy_extends.product_product_iva_acreditable'), 'amount': amount_tax},
            {'product': self.env.ref('l10n_cr_toy_extends.product_product_arancel'), 'amount': amount_tlc},
        ]

        array_line = []
        for product in PRODUCTS:
            self.ensure_one()
            data = {
                'name': product['product'].name,
                'product_id': product['product'].id,
                'product_uom_id': product['product'].uom_id.id,
                'quantity':1,
                'price_unit': product['amount'],
                'tax_ids': [],
            }

            array_line.append((0,0,data))

        return array_line


    def _prepare_invoice_by_hacienda(self,change_is):
        """Prepare the dict of values to create the new invoice for a purchase order.
        """
        self.ensure_one()
        move_type = self._context.get('default_move_type', 'in_invoice')
        journal = self.env['account.move'].with_context(default_move_type=move_type)._get_default_journal()
        if not journal:
            raise UserError(_('Please define an accounting purchase journal for the company %s (%s).') % (self.company_id.name, self.company_id.id))

        partner_invoice_id = self.env.ref('l10n_cr_toy_extends.res_partner_hacienda')

        invoice_vals = {
            'ref': self.partner_ref or '',
            'move_type': move_type,
            'narration': self.notes,
            'currency_id': self.company_id.currency_id.id,
            'invoice_user_id': self.user_id and self.user_id.id,
            'partner_id': partner_invoice_id.id,
            'fiscal_position_id': (self.fiscal_position_id or self.fiscal_position_id.get_fiscal_position(partner_invoice_id.id)).id,
            'payment_reference': self.partner_ref or '',
            'partner_bank_id': partner_invoice_id.bank_ids[:1].id,
            'invoice_origin': self.name,
            'invoice_payment_term_id': self.payment_term_id.id,
            'invoice_line_ids': [],
            'company_id': self.company_id.id,
        }
        return invoice_vals


    def apply_yes_tlc_lines(self):
        for record in self:
            if record.order_line:
                record.order_line.write({'apply_tlc': True})

    def apply_not_tlc_lines(self):
        for record in self:
            if record.order_line:
                record.order_line.write({'apply_tlc': False})

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    product_packaging = fields.Many2one('product.packaging', string='Paquete', default=False, check_company=True)
    metro_cubico = fields.Float(string=u'M³', store=True, compute='_computed_metro_cubico')
    package_id = fields.Many2one('product.packaging',string='Paquete')
    package_qty = fields.Float('Contenido', related='package_id.qty')
    package_qty_in = fields.Float('Cant.Paquetes', default=0.0)
    package_qty_unit = fields.Float(store=True, compute='_compute_package_qty_unit')
    code_supplier = fields.Char(related='product_id.code_supplier', string='Código compra')
    price_last = fields.Monetary(string='Precio anterior', store=True, copy=False)
    apply_tlc = fields.Boolean('TLC aplica')



    @api.onchange('product_packaging')
    def _onchange_product_packaging(self):
        if self.product_packaging:
            return self._check_package()

    def _check_package(self):
        default_uom = self.product_id.uom_id
        pack = self.product_packaging
        qty = self.product_qty
        q = default_uom._compute_quantity(pack.qty, self.product_uom)
        # We do not use the modulo operator to check if qty is a mltiple of q. Indeed the quantity
        # per package might be a float, leading to incorrect results. For example:
        # 8 % 1.6 = 1.5999999999999996
        # 5.4 % 1.8 = 2.220446049250313e-16
        if (qty and q and float_compare(qty / q, float_round(qty / q, precision_rounding=1.0), precision_rounding=0.001)!= 0):
            newqty = qty - (qty % q) + q
            return {
                'warning': {
                    'title': _('Ups'),
                    'message': _(
                        "Este producto está empaquetado por %(pack_size).2f %(pack_name)s. Debería comprar %(quantity).2f %(unit)s.",
                        pack_size=pack.qty,
                        pack_name=default_uom.name,
                        quantity=newqty,
                        unit=self.product_uom.name
                    ),
                },
            }
        return {}

    @api.depends('product_qty', 'product_packaging','product_id.volume')
    def _computed_metro_cubico(self):
        self._calc_metro_cubico()

    def _calc_metro_cubico(self):
        for line in self:
            if line.product_id.volume == 0.0 and line.product_packaging:
                raise UserError(
                    _('El producto no tiene un volumen. Por favor, asegúrse de ingresar el campo volumen para calcular los métros cúbicos.'))
            if line.product_id.volume > 0.0 and line.product_packaging:
                if line.product_qty % line.product_packaging.qty != 0:
                    raise UserError(_('La cantidad ingresada debe ser múltiplo de la cantidad especificada en el empaquetado !'))
            volume = line.product_id.volume
            qty = line.product_qty
            m3 = volume * qty
            line.metro_cubico = m3

    @api.onchange('product_id')
    def onchange_product_id(self):
        super(PurchaseOrderLine, self).onchange_product_id()
        for record in self:
            if record.product_id:
                if record.product_id.packaging_ids:
                    paquete_id = record.product_id.packaging_ids[0]
                    if paquete_id:
                        record.package_id = paquete_id
                aml = self.env['account.move.line'].sudo().search([('product_id', '=', record.product_id.id),
                                                                   ('move_id.state', '=', 'posted'),
                                                                   ('move_id.reversed_entry_id','=',False)
                                                                   ], limit=1, order='id desc')
                if aml:
                    price_unit = aml.price_unit
                    record.price_last = price_unit

    @api.depends('product_id','package_id','package_qty','package_qty_in')
    def _compute_package_qty_unit(self):
        for record in self:
            package_qty_purchase = 0.0
            if record.product_id and record.package_id and record.package_qty and record.package_qty_in:
                package_qty_purchase = record.package_qty * record.package_qty_in

            record.package_qty_unit = package_qty_purchase

    @api.onchange('package_qty_unit')
    def onchange_package_qty_unit(self):
        for record in self:
            record.product_qty = record.package_qty_unit