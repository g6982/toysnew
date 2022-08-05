# -*- coding: utf-8 -*-
import base64
import datetime
import logging
from odoo.tools.misc import formatLang
from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

from random import randint
from odoo.tools import float_is_zero

class PosOrder(models.Model):
    _inherit = "pos.order"

    applied_coupon_ids = fields.One2many('coupon.coupon', 'pos_sales_order_id', string="Applied Coupons", copy=False)
    generated_coupon_ids = fields.One2many('coupon.coupon', 'pos_order_id', string="Offered Coupons", copy=False)
    reward_amount = fields.Float(compute='_compute_reward_total')
    no_code_promo_program_ids = fields.Many2many('coupon.program', string="Applied Immediate Promo Programs",
                                                 domain="[('promo_code_usage', '=', 'no_code_needed'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]", copy=False)
    code_promo_program_id = fields.Many2one('coupon.program', string="Applied Promo Program",
                                            domain="[('promo_code_usage', '=', 'code_needed'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]", copy=False)
    promo_code = fields.Char(related='code_promo_program_id.promo_code', help="Applied program code", readonly=False)

    @api.depends('lines')
    def _compute_reward_total(self):
        for order in self:
            order.reward_amount = sum([line.price_subtotal for line in order._get_reward_lines()])

    def _get_no_effect_on_threshold_lines(self):
        self.ensure_one()
        lines = self.env['pos.order.line']
        return lines

    def recompute_coupon_lines(self):
        for order in self:
            order._remove_invalid_reward_lines()
            order._create_new_no_code_promo_reward_lines()
            order._update_existing_reward_lines()


    def _get_reward_lines(self):
        self.ensure_one()
        return self.lines.filtered(lambda line: line.is_reward_line)


    def _update_existing_reward_lines(self):
        '''Update values for already applied rewards'''
        def update_line(order, lines, values):
            '''Update the lines and return them if they should be deleted'''
            lines_to_remove = self.env['pos.order.line']
            # Check commit 6bb42904a03 for next if/else
            # Remove reward line if price or qty equal to 0
            if values['qty'] and values['price_unit']:
                lines.write(values)
            else:
                if program.reward_type != 'free_shipping':
                    # Can't remove the lines directly as we might be in a recordset loop
                    lines_to_remove += lines
                else:
                    values.update(price_unit=0.0)
                    lines.write(values)
            return lines_to_remove

        self.ensure_one()
        order = self
        applied_programs = order._get_applied_programs_with_rewards_on_current_order()
        for program in applied_programs:
            values = order._get_reward_line_values_pos(program)
            lines = order.order_line.filtered(lambda line: line.product_id == program.discount_line_product_id)
            if program.reward_type == 'discount' and program.discount_type == 'percentage':
                lines_to_remove = lines
                # Values is what discount lines should really be, lines is what we got in the SO at the moment
                # 1. If values & lines match, we should update the line (or delete it if no qty or price?)
                # 2. If the value is not in the lines, we should add it
                # 3. if the lines contains a tax not in value, we should remove it
                for value in values:
                    value_found = False
                    for line in lines:
                        # Case 1.
                        if not len(set(line.tax_ids.mapped('id')).symmetric_difference(set([v[1] for v in value['tax_ids']]))):
                            value_found = True
                            # Working on Case 3.
                            lines_to_remove -= line
                            lines_to_remove += update_line(order, line, value)
                            continue
                    # Case 2.
                    if not value_found:
                        order.write({'lines': [(0, False, value)]})
                # Case 3.
                lines_to_remove.unlink()
            else:
                update_line(order, lines, values[0]).unlink()

    def _remove_invalid_reward_lines(self):
        self.ensure_one()
        order = self

        applied_programs = order._get_applied_programs()
        applicable_programs = self.env['coupon.program']
        if applied_programs:
            applicable_programs = order._get_applicable_programs() + order._get_valid_applied_coupon_program()
            applicable_programs = applicable_programs._keep_only_most_interesting_auto_applied_global_discount_program()
        programs_to_remove = applied_programs - applicable_programs

        reward_product_ids = applied_programs.discount_line_product_id.ids
        # delete reward line coming from an archived coupon (it will never be updated/removed when recomputing the order)
        if order._name == 'pos.order':
            invalid_lines = order.lines.filtered(lambda line: line.is_reward_line and line.product_id.id not in reward_product_ids)
        else:
            invalid_lines = order.order_line.filtered(lambda line: line.is_reward_line and line.product_id.id not in reward_product_ids)

        if programs_to_remove:
            product_ids_to_remove = programs_to_remove.discount_line_product_id.ids

            if product_ids_to_remove:
                # Invalid generated coupon for which we are not eligible anymore ('expired' since it is specific to this SO and we may again met the requirements)
                self.generated_coupon_ids.filtered(lambda coupon: coupon.program_id.discount_line_product_id.id in product_ids_to_remove).write({'state': 'expired'})

            # Reset applied coupons for which we are not eligible anymore ('valid' so it can be use on another )
            coupons_to_remove = order.applied_coupon_ids.filtered(lambda coupon: coupon.program_id in programs_to_remove)
            coupons_to_remove.write({'state': 'new'})

            # Unbind promotion and coupon programs which requirements are not met anymore
            order.no_code_promo_program_ids -= programs_to_remove
            order.code_promo_program_id -= programs_to_remove

            if coupons_to_remove:
                order.applied_coupon_ids -= coupons_to_remove

            # Remove their reward lines
            if product_ids_to_remove:
                if order._name == 'pos.order':
                    invalid_lines |= order.lines.filtered(lambda line: line.product_id.id in product_ids_to_remove)
                else:
                    invalid_lines |= order.order_line.filtered(lambda line: line.product_id.id in product_ids_to_remove)

        invalid_lines.unlink()

    def _get_applied_programs(self):
        return self.code_promo_program_id + self.no_code_promo_program_ids + self.applied_coupon_ids.mapped('program_id')

    def _is_reward_in_order_lines_pos(self, program):
        self.ensure_one()
        order_quantity = sum(self.lines.filtered(lambda line:
                                                      line.product_id == program.reward_product_id).mapped('qty'))
        return order_quantity >= program.reward_product_quantity

    def _get_applicable_programs(self):
        """
        This method is used to return the valid applicable programs on given order.
        """
        self.ensure_one()
        programs = self.env['coupon.program'].with_context(no_outdated_coupons=True,).search([
            ('company_id', 'in', [self.company_id.id, False]),
            '|', ('rule_date_from', '=', False), ('rule_date_from', '<=', self.date_order),
            '|', ('rule_date_to', '=', False), ('rule_date_to', '>=', self.date_order),
        ], order="id")._filter_programs_from_common_pos_rules(self)

        return programs

    def _get_applicable_no_code_promo_program(self):
        self.ensure_one()
        programs = self.env['coupon.program'].with_context(
            no_outdated_coupons=True,
            applicable_coupon=True,
        ).search([
            ('promo_code_usage', '=', 'no_code_needed'),
            '|', ('rule_date_from', '=', False), ('rule_date_from', '<=', self.date_order),
            '|', ('rule_date_to', '=', False), ('rule_date_to', '>=', self.date_order),
            '|', ('company_id', '=', self.company_id.id), ('company_id', '=', False),
        ])._filter_programs_from_common_pos_rules(self)
        return programs


    def _get_valid_applied_coupon_program(self):
        self.ensure_one()
        programs = self.applied_coupon_ids.mapped('program_id').filtered(lambda p: p.promo_applicability == 'on_next_order')._filter_programs_from_common_pos_rules(self, True)
        return programs

    def _create_new_no_code_promo_reward_lines(self):
        '''Apply new programs that are applicable'''
        self.ensure_one()
        order = self
        programs = order._get_applicable_no_code_promo_program()
        programs = programs._keep_only_most_interesting_auto_applied_global_discount_program()
        for program in programs:
            # VFE REF in master _get_applicable_no_code_programs already filters programs
            # why do we need to reapply this bunch of checks in _check_promo_code ????
            # We should only apply a little part of the checks in _check_promo_code...
            error_status = program._check_promo_code(order, False)
            if not error_status.get('error'):
                if program.promo_applicability == 'on_next_order':
                    order.state != 'cancel' and order._create_reward_coupon(program)
                elif program.discount_line_product_id.id not in self.order_line.mapped('product_id').ids:
                    self.write({'lines': [(0, False, value) for value in self._get_reward_line_values_pos(program)]})
                order.no_code_promo_program_ids |= program

    def _is_reward_in_pos_order_lines(self, program):
        self.ensure_one()
        if self._name == 'pos.order':
            order_quantity = sum(self.lines.filtered(lambda line:
                                                          line.product_id == program.reward_product_id).mapped('qty'))
        else:
            order_quantity = sum(self.order_line.filtered(lambda line:
                                                          line.product_id == program.reward_product_id).mapped('product_uom_qty'))
        return order_quantity >= program.reward_product_quantity

    def _get_no_effect_on_threshold_pos_lines(self):
        self.ensure_one()
        lines = self.env['pos.order.line']
        return lines

    def _get_applied_programs_with_rewards_on_current_order(self):
        return self.no_code_promo_program_ids.filtered(lambda p: p.promo_applicability == 'on_current_order') + \
               self.applied_coupon_ids.mapped('program_id') + \
               self.code_promo_program_id.filtered(lambda p: p.promo_applicability == 'on_current_order')

    def _get_applied_programs_with_rewards_on_next_order(self):
        return self.no_code_promo_program_ids.filtered(lambda p: p.promo_applicability == 'on_next_order') + \
               self.code_promo_program_id.filtered(lambda p: p.promo_applicability == 'on_next_order')



    def _is_global_discount_already_applied(self):
        applied_programs = self.no_code_promo_program_ids + \
                           self.code_promo_program_id + \
                           self.applied_coupon_ids.mapped('program_id')
        return applied_programs.filtered(lambda program: program._is_global_discount_program())

    def _create_reward_line_pos(self, program):
        self.write({'lines': [(0, False, value) for value in self._get_reward_line_values_pos(program)]})

    def _get_reward_line_values_pos(self, program):
        self.ensure_one()
        self = self.with_context(lang=self.partner_id.lang)
        program = program.with_context(lang=self.partner_id.lang)
        if program.reward_type == 'discount':
            return self._get_reward_values_discount_pos(program)
        elif program.reward_type == 'product':
            return [self._get_reward_values_product_pos(program)]


    def _get_base_order_lines(self, program):
        """ Returns the sale order lines not linked to the given program.
        """
        return self.lines.filtered(lambda x: not (x.is_reward_line and x.product_id == program.discount_line_product_id))

    def _get_reward_values_discount_fixed_amount(self, program):
        total_amount = sum(self._get_base_order_lines(program).mapped('price_subtotal_incl'))
        fixed_amount = program._compute_program_amount('discount_fixed_amount', self.currency_id)
        if total_amount < fixed_amount:
            return total_amount
        else:
            return fixed_amount

    def _get_reward_values_discount_pos(self, program):
        if program.discount_type == 'fixed_amount':
            taxes = program.discount_line_product_id.taxes_id
            if self.fiscal_position_id:
                taxes = self.fiscal_position_id.map_tax(taxes)

            price_unit = self._get_reward_values_discount_fixed_amount(program)

            fpos = self.fiscal_position_id
            tax_ids_after_fiscal_position = fpos.map_tax(taxes, program.discount_line_product_id, self.partner_id)
            price = (- price_unit) * (1 - 0.0 / 100.0)
            calc_taxes = tax_ids_after_fiscal_position.compute_all(price, self.pricelist_id.currency_id, 1.0, product=program.discount_line_product_id,
                                                                   partner=self.partner_id)

            return [{
                'full_product_name': _("Producto %s - Discount: %s" % (program.discount_line_product_id.name,program.name)),
                'product_id': program.discount_line_product_id.id,
                'price_unit': - price_unit,
                'qty': 1.0,
                'product_uom_id': program.discount_line_product_id.uom_id.id,
                'is_reward_line': True,
                'tax_ids': [(4, tax.id, False) for tax in taxes],
                'price_subtotal': calc_taxes['total_excluded'],
                'price_subtotal_incl': calc_taxes['total_included'],
            }]
        reward_dict = {}
        lines = self._get_paid_order_lines()
        amount_total = sum(self._get_base_order_lines(program).mapped('price_subtotal'))
        if program.discount_apply_on == 'cheapest_product':
            line = self._get_cheapest_line()
            if line:
                discount_line_amount = min(line.price_reduce * (program.discount_percentage / 100), amount_total)
                if discount_line_amount:
                    taxes = self.fiscal_position_id.map_tax(line.tax_ids)

                    fpos = line.order_id.fiscal_position_id
                    tax_ids_after_fiscal_position = fpos.map_tax(taxes, program.discount_line_product_id, line.order_id.partner_id)
                    price = (- discount_line_amount if discount_line_amount > 0 else 0) * (1 - 0.0 / 100.0)
                    calc_taxes = tax_ids_after_fiscal_position.compute_all(price, line.order_id.pricelist_id.currency_id, 1.0, product=program.discount_line_product_id,
                                                                           partner=line.order_id.partner_id)

                    reward_dict[line.tax_id] = {
                        'full_product_name': _("Producto %s - Discount: %s" % (program.discount_line_product_id.name, program.name)),
                        'product_id': program.discount_line_product_id.id,
                        'price_unit': - discount_line_amount if discount_line_amount > 0 else 0,
                        'qty': 1.0,
                        'product_uom_id': program.discount_line_product_id.uom_id.id,
                        'is_reward_line': True,
                        'tax_ids': [(4, tax.id, False) for tax in taxes],
                        'price_subtotal': calc_taxes['total_excluded'],
                        'price_subtotal_incl': calc_taxes['total_included'],
                    }
        elif program.discount_apply_on in ['specific_products', 'on_order']:
            if program.discount_apply_on == 'specific_products':
                # We should not exclude reward line that offer this product since we need to offer only the discount on the real paid product (regular product - free product)
                free_product_lines = self.env['coupon.program'].search([('reward_type', '=', 'product'), ('reward_product_id', 'in', program.discount_specific_product_ids.ids)]).mapped('discount_line_product_id')
                lines = lines.filtered(lambda x: x.product_id in (program.discount_specific_product_ids | free_product_lines))

            # when processing lines we should not discount more than the order remaining total
            currently_discounted_amount = 0
            for line in lines:
                discount_line_amount = min(self._get_reward_values_discount_percentage_per_line(program, line), amount_total - currently_discounted_amount)

                if discount_line_amount:

                    if line.tax_ids in reward_dict:
                        reward_dict[line.tax_ids]['price_unit'] -= discount_line_amount
                    else:
                        taxes = self.fiscal_position_id.map_tax(line.tax_ids)

                        fpos = line.order_id.fiscal_position_id
                        tax_ids_after_fiscal_position = fpos.map_tax(taxes, program.discount_line_product_id, line.order_id.partner_id)
                        price = (- discount_line_amount if discount_line_amount > 0 else 0) * (1 - 0.0 / 100.0)
                        calc_taxes = tax_ids_after_fiscal_position.compute_all(price, line.order_id.pricelist_id.currency_id, 1.0, product=program.discount_line_product_id,
                                                                          partner=line.order_id.partner_id)

                        reward_dict[line.tax_ids] = {
                            'full_product_name': _(
                                "Producto %(product)s  - Discount: %(program)s - On product with following taxes: %(taxes)s",
                                product=program.discount_line_product_id.name,
                                program=program.name,
                                taxes=", ".join(taxes.mapped('name')),
                            ),
                            'product_id': program.discount_line_product_id.id,
                            'price_unit': - discount_line_amount if discount_line_amount > 0 else 0,
                            'qty': 1.0,
                            'product_uom_id': program.discount_line_product_id.uom_id.id,
                            'is_reward_line': True,
                            'tax_ids': [(4, tax.id, False) for tax in taxes],
                            'price_subtotal': calc_taxes['total_excluded'],
                            'price_subtotal_incl': calc_taxes['total_included'],
                        }
                        currently_discounted_amount += discount_line_amount

        # If there is a max amount for discount, we might have to limit some discount lines or completely remove some lines
        max_amount = program._compute_program_amount('discount_max_amount', self.currency_id)
        if max_amount > 0:
            amount_already_given = 0
            for val in list(reward_dict):
                amount_to_discount = amount_already_given + reward_dict[val]["price_unit"]
                if abs(amount_to_discount) > max_amount:
                    reward_dict[val]["price_unit"] = - (max_amount - abs(amount_already_given))
                    add_name = formatLang(self.env, max_amount, currency_obj=self.currency_id)
                    reward_dict[val]["name"] += "( " + _("limited to ") + add_name + ")"
                amount_already_given += reward_dict[val]["price_unit"]
                if reward_dict[val]["price_unit"] == 0:
                    del reward_dict[val]
        return reward_dict.values()

    def _get_reward_values_product_pos(self, program):
        price_unit = self.lines.filtered(lambda line: program.reward_product_id == line.product_id)[0].price_reduce

        lines = (self.lines - self._get_reward_lines()).filtered(lambda x: program._get_valid_products(x.product_id))
        max_product_qty = sum(lines.mapped('qty')) or 1
        total_qty = sum(self.lines.filtered(lambda x: x.product_id == program.reward_product_id).mapped('qty'))
        # Remove needed quantity from reward quantity if same reward and rule product
        if program._get_valid_products(program.reward_product_id):
            # number of times the program should be applied
            program_in_order = max_product_qty // (program.rule_min_quantity + program.reward_product_quantity)
            # multipled by the reward qty
            reward_product_qty = program.reward_product_quantity * program_in_order
            # do not give more free reward than products
            reward_product_qty = min(reward_product_qty, total_qty)
            if program.rule_minimum_amount:
                order_total = sum(lines.mapped('price_total')) - (program.reward_product_quantity * program.reward_product_id.lst_price)
                reward_product_qty = min(reward_product_qty, order_total // program.rule_minimum_amount)
        else:
            reward_product_qty = min(max_product_qty, total_qty)

        reward_qty = min(int(int(max_product_qty / program.rule_min_quantity) * program.reward_product_quantity), reward_product_qty)
        # Take the default taxes on the reward product, mapped with the fiscal position
        taxes = self.fiscal_position_id.map_tax(program.reward_product_id.taxes_id)

        fpos = self.fiscal_position_id
        tax_ids_after_fiscal_position = fpos.map_tax(taxes, program.discount_line_product_id, self.partner_id)
        price = (- price_unit) * (1 - 0.0 / 100.0)
        calc_taxes = tax_ids_after_fiscal_position.compute_all(price, self.pricelist_id.currency_id, 1.0, product=program.discount_line_product_id,
                                                               partner=self.partner_id)

        return {
            'full_product_name': _(
                "Producto %(product)s  -  Discount: %(program)s - On product with following taxes: %(taxes)s",
                product=program.discount_line_product_id.name,
                program=program.name,
                taxes=", ".join(taxes.mapped('name')),
            ),
            'product_id': program.discount_line_product_id.id,
            'price_unit': - price_unit,
            'qty': reward_qty,
            'product_uom_id':  program.reward_product_id.uom_id.id,
            'is_reward_line': True,
            'tax_ids': [(4, tax.id, False) for tax in taxes],
            'price_subtotal': calc_taxes['total_excluded'],
            'price_subtotal_incl': calc_taxes['total_included'],

        }

    def _get_base_order_lines(self, program):
        """ Returns the sale order lines not linked to the given program.
        """
        return self.lines.filtered(lambda x: not (x.is_reward_line and x.product_id == program.discount_line_product_id))

    def _get_cheapest_line(self):
        # Unit prices tax included
        return min(self.lines.filtered(lambda x: not x.is_reward_line and x.price_reduce > 0), key=lambda x: x['price_reduce'])

    def _get_paid_order_lines(self):
        """ Returns the sale order lines that are not reward lines.
            It will also return reward lines being free product lines. """
        free_reward_product = self.env['coupon.program'].search([('reward_type', '=', 'product')]).mapped('discount_line_product_id')
        return self.lines.filtered(lambda x: not x.is_reward_line or x.product_id in free_reward_product)

    def _get_reward_values_discount_percentage_per_line(self, program, line):
        discount_amount = line.qty * line.price_reduce * (program.discount_percentage / 100)
        return discount_amount

    @api.onchange('payment_ids', 'lines')
    def _onchange_amount_all(self):
        for order in self:
            currency = order.pricelist_id.currency_id
            order.amount_paid = sum(payment.amount for payment in order.payment_ids)
            order.amount_return = sum(payment.amount < 0 and payment.amount or 0 for payment in order.payment_ids)
            amount_tax = 0.0
            if order.lines:
                for line in order.lines:
                    total = order._amount_line_tax(line, order.fiscal_position_id)
                    amount_tax += total
            order.amount_tax = amount_tax
            amount_untaxed = 0.0
            if order.lines:
                amount_untaxed = currency.round(sum(line.price_subtotal for line in order.lines))
            order.amount_total = order.amount_tax + amount_untaxed


    #************************************************ APLICACION DE CUPONES Y PROMOCIONES DESDE POS ***********************************************
    @api.model
    def create_provisional_order(self, order, coupon_code):

        company_id = self.env['res.company'].sudo().browse(order.get('company_id'))
        config_id = self.env['pos.config'].sudo().browse(order.get('config_id'))
        default_fiscal_position = config_id.default_fiscal_position_id
        customer = False
        if order.get('partner_id'):
            customer = self.env['res.partner'].sudo().browse(order.get('partner_id'))
        fiscal_position = customer.property_account_position_id if customer else default_fiscal_position
        pricelist_id = self.env['product.pricelist'].sudo().browse(order.get('pricelist_id'))

        def create_order_line(lines):
            array_lines = []
            amount_total = 0.0
            sub_total = 0.0
            amount_tax = 0.0
            for l in lines:
                product = self.env['product.product'].sudo().browse(l.get('product_id'))
                price_unit = l.get('price_unit')
                #price_unit = pricelist_id.get_product_price(product, l.get('qty'), False)
                tax_ids = fiscal_position.map_tax(product.taxes_id)
                tax_values = (
                    tax_ids.compute_all(price_unit, company_id.currency_id, l.get('qty'))
                    if tax_ids
                    else {
                        'total_excluded': price_unit * l.get('qty'),
                        'total_included': price_unit * l.get('qty'),
                    }
                )

                data = {
                    'full_product_name': 'Producto' + str(product.name) + ' - ' + l.get('full_product_name'),
                    'discount': l.get('discount'),
                    'pack_lot_ids': [],
                    'price_unit': price_unit,
                    'product_id': product.id,
                    'price_subtotal': tax_values['total_excluded'],
                    'price_subtotal_incl': tax_values['total_included'],
                    'qty': l.get('qty'),
                    'tax_ids': [(6, 0, tax_ids.ids)]
                }
                array_lines.append((0, 0, data))

                amount_total += data['price_subtotal_incl']
                sub_total += data['price_subtotal']

            amount_tax = amount_total - sub_total

            return array_lines, amount_total, amount_tax

        lines, amount_total, amount_tax = create_order_line(order.get('lines'))

        order = self.env[self._name].create({
            'company_id': order.get('company_id'),
            'session_id': order.get('session_id'),
            'partner_id': order.get('partner_id'),
            'pricelist_id': order.get('pricelist_id'),
            'lines': lines,
            'amount_paid': 0,
            'amount_return': 0,
            'amount_tax': amount_tax,
            'amount_total': amount_total,
            'pos_reference': 'Orden' + str(order.get('uid')),
            'envio_hacienda': False
        })

        if order:
            lines_res = self.process_coupon_by_pos(order, coupon_code)
            res = []
            total_array = []
            for value in lines_res:
                res.append(value)
            total_array.append(order.amount_total)

            order.lines.unlink()
            order.unlink()

            return [res,total_array]

    def process_coupon_by_pos(self, pos_order, coupon_code):

        error_status = self.apply_coupon_by_pos(pos_order, coupon_code)
        if type(error_status) == dict:
            if error_status.get('error', False):
                raise UserError(error_status.get('error', False))
            if error_status.get('not_found', False):
                raise UserError(error_status.get('not_found', False))
        else:
            return error_status #En realidad devuelve el resultado.

    def apply_coupon_by_pos(self, order, coupon_code):
        error_status = {}
        program = self.env['coupon.program'].search([('promo_code', '=', coupon_code)])
        if program:
            error_status = program._check_promo_code_pos(order, coupon_code)
            if not error_status:
                if program.promo_applicability == 'on_next_order':
                    # Avoid creating the coupon if it already exist
                    if program.discount_line_product_id.id not in order.generated_coupon_ids.filtered(lambda coupon: coupon.state in ['new', 'reserved']).mapped('discount_line_product_id').ids:
                        coupon = order._create_reward_coupon(program)
                        return {
                            'generated_coupon': {
                                'reward': coupon.program_id.discount_line_product_id.name,
                                'code': coupon.code,
                            }
                        }
                else:  # The program is applied on this order
                    return order._create_reward_line_pos_js(program)
                    #order.code_promo_program_id = program
        else:
            coupon = self.env['coupon.coupon'].search([('code', '=', coupon_code)], limit=1)
            if coupon:
                error_status = coupon._check_coupon_code_pos(order)
                if not error_status:
                    return order._create_reward_line_pos_js(coupon.program_id)
                    #order.applied_coupon_ids += coupon
                    #coupon.write({'state': 'used'})
            else:
                error_status = {'not_found': _('This coupon is invalid (%s).') % (coupon_code)}
        return error_status


    def _create_reward_line_pos_js(self, program):
        return self._get_reward_line_values_pos(program)

    @api.model
    def _order_fields(self, ui_order):
        vals = super(PosOrder, self)._order_fields(ui_order)
        vals["note"] = ui_order.get("note")
        return vals

    @api.model
    def _process_order(self, order, draft, existing_order):
        #Para retorno (Nota de crédito POS)
        data = order.get('data')
        if data.get('is_return_order'):
            data['amount_paid'] = 0
            for line in data.get('lines'):
                line_dict = line[2]
                line_dict['qty'] = line_dict['qty']
                if line_dict.get('original_line_id'):
                    original_line = self.env['pos.order.line'].browse(line_dict.get('original_line_id'))
                    original_line.line_qty_returned += abs(line_dict['qty'])
            for statement in data.get('statement_ids'):
                statement_dict = statement[2]
                if data['amount_total'] < 0:
                    statement_dict['amount'] = statement_dict['amount'] * -1
                else:
                    statement_dict['amount'] = statement_dict['amount']
            if data['amount_total'] < 0:
                data['amount_tax'] = data.get('amount_tax')
                data['amount_return'] = 0
                data['amount_total'] = data.get('amount_total')
        # Fin retorno (Nota de crédito POS)

        order_id = super(PosOrder, self)._process_order(order, draft, existing_order)
        pos_order = self.env['pos.order'].sudo().browse(order_id)
        if pos_order:
            if 'coupon_code' in order['data']:
                coupon_code = order['data']['coupon_code']
                program = self.env['coupon.program'].search([('promo_code', '=', coupon_code)])
                if program:
                    pos_order.code_promo_program_id = program
                else:
                    coupon = self.env['coupon.coupon'].search([('code', '=', coupon_code)], limit=1)
                    if coupon:
                        pos_order.applied_coupon_ids += coupon
                        coupon.write({'state': 'used'})

        return order_id

        # if existing_order and existing_order.display_name == '/' and 'envio_hacienda' in order['data']:
        #     if order['data']['envio_hacienda']:
        #         o = self.env['pos.order'].sudo().browse(existing_order.id)
        #         o.sudo().lines.unlink()
        #         o.sudo().unlink()
        #         existing_order = False
        # return super(PosOrder, self)._process_order(order, draft, existing_order)


    #TODO: AJUSTE DE PAGOS
    @api.model
    def _payment_fields(self, order, ui_paymentline):
        payment_date = ui_paymentline['name']
        payment_date = fields.Date.context_today(self, fields.Datetime.from_string(payment_date))
        amount_paid, amount_real = self._refactor_amount(order,ui_paymentline)
        return {
            'amount': amount_paid,
            'amount_real': amount_real,
            'payment_date': payment_date,
            'payment_method_id': ui_paymentline['payment_method_id'],
            'card_type': ui_paymentline.get('card_type'),
            'transaction_id': ui_paymentline.get('transaction_id'),
            'branch_id':order.branch_id.id,
            'pos_order_id': order.id,
            'session_id': order.session_id.id
        }

    @api.model
    def _refactor_amount(self,order,ui_paymentline):
        amount_paid = 0.0
        if order.payment_ids:
            paid_last = sum(p.amount for p in order.payment_ids)
            saldo = order.amount_total - order.amount_paid
            if (ui_paymentline['amount'] or 0.0) >= saldo:
                amount_paid = saldo
            else:
                amount_paid = ui_paymentline['amount'] or 0.0
            #amount_paid_now = order.amount_paid - paid_last
            #amount_paid = amount_paid_now
        elif order.amount_paid > (ui_paymentline['amount'] or 0.0):
            amount_paid = ui_paymentline['amount'] or 0.0
        else:
            amount_paid = order.amount_paid

        return amount_paid, (ui_paymentline['amount'] or 0.0)


    def _process_payment_lines(self, pos_order, order, pos_session, draft):
        prec_acc = order.pricelist_id.currency_id.decimal_places

        order_bank_statement_lines= self.env['pos.payment'].search([('pos_order_id', '=', order.id)])
        order_bank_statement_lines.unlink()
        for payments in pos_order['statement_ids']:
            if not float_is_zero(payments[2]['amount'], precision_digits=prec_acc):
                order.add_payment(self._payment_fields(order, payments[2]))

        order.amount_paid = sum(order.payment_ids.mapped('amount'))

        # if not draft and not float_is_zero(pos_order['amount_return'], prec_acc):
        #     cash_payment_method = pos_session.payment_method_ids.filtered('is_cash_count')[:1]
        #     if not cash_payment_method:
        #         raise UserError(_("No cash statement found for this session. Unable to record returned cash."))
        #     return_payment_vals = {
        #         'name': _('return'),
        #         'pos_order_id': order.id,
        #         'branch_id' : order.branch_id.id,
        #         'amount': -pos_order['amount_return'],
        #         'payment_date': fields.Date.context_today(self),
        #         'payment_method_id': cash_payment_method.id,
        #     }
        #     order.add_payment(return_payment_vals)

    #RE-IMPRESI
    def print_pos_receipt(self):
        orderlines = []
        paymentlines = []
        discount = 0

        for orderline in self.lines:
            new_vals = {
                'product_id': orderline.product_id.name,
                'total_price': orderline.price_subtotal_incl,
                'qty': orderline.qty,
                'price_unit': orderline.price_unit,
                'discount': orderline.discount,
            }

            discount += (orderline.price_unit * orderline.qty * orderline.discount) / 100
            orderlines.append(new_vals)

        for payment in self.payment_ids:
            if payment.amount > 0:
                temp = {
                    'amount': payment.amount,
                    'name': payment.payment_method_id.name
                }
                paymentlines.append(temp)

        client = {
            'name': self.partner_id.name,
            'document': self.partner_id.identification_id.name if self.partner_id.identification_id else 'Documento',
            'vat': self.partner_id.vat,
            'email': self.partner_id.email,
        }

        tipo_documento = ''
        if self.tipo_documento == 'TE':
            tipo_documento = 'TIQUETE ELECTRÓNICO'
        elif self.tipo_documento == 'FE':
            tipo_documento = 'FACTURA ELECTRÓNICA'


        vals = {
            'discount': discount,
            'orderlines': orderlines,
            'paymentlines': paymentlines,
            'change': self.amount_return,
            'subtotal': self.amount_total - self.amount_tax,
            'tax': self.amount_tax,
            'amount_total': self.amount_total,
            'saldo': self.amount_total - self.amount_paid,
            'barcode': self.barcode,
            'user_name': self.user_id.name,
            'tipo_documento': tipo_documento,
            'client': client,
            'secuencia': self.sequence,
            'numero_electronico': self.number_electronic,
        }

        return vals