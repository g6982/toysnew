# -*- coding: utf-8 -*-
from odoo import api, fields, models, _



class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    is_reward_line = fields.Boolean('Is a program reward line')
    price_reduce = fields.Float(compute='_get_price_reduce', string='Price Reduce', digits='Product Price', readonly=True, store=True)

    def unlink(self):
        related_program_lines = self.env['pos.order.line']
        # Reactivate coupons related to unlinked reward line
        for line in self.filtered(lambda line: line.is_reward_line):
            coupons_to_reactivate = line.order_id.applied_coupon_ids.filtered(
                lambda coupon: coupon.program_id.discount_line_product_id == line.product_id
            )
            coupons_to_reactivate.write({'state': 'new'})
            line.order_id.applied_coupon_ids -= coupons_to_reactivate
            # Remove the program from the order if the deleted line is the reward line of the program
            # And delete the other lines from this program (It's the case when discount is split per different taxes)
            related_program = self.env['coupon.program'].search([('discount_line_product_id', '=', line.product_id.id)])
            if related_program:
                line.order_id.no_code_promo_program_ids -= related_program
                line.order_id.code_promo_program_id -= related_program
                related_program_lines |= line.order_id.lines.filtered(lambda l: l.product_id.id == related_program.discount_line_product_id.id) - line
        return super(PosOrderLine, self | related_program_lines).unlink()

    def _compute_tax_id(self):
        reward_lines = self.filtered('is_reward_line')
        super(PosOrderLine, self - reward_lines)._compute_tax_id()
        # Discount reward line is split per tax, the discount is set on the line but not on the product
        # as the product is the generic discount line.
        # In case of a free product, retrieving the tax on the line instead of the product won't affect the behavior.
        for line in reward_lines:
            line = line.with_company(line.company_id)
            fpos = line.order_id.fiscal_position_id or line.order_id.fiscal_position_id.get_fiscal_position(line.order_partner_id.id)
            # If company_id is set, always filter taxes by the company
            taxes = line.tax_id.filtered(lambda r: not line.company_id or r.company_id == line.company_id)
            line.tax_id = fpos.map_tax(taxes, line.product_id, line.order_id.partner_shipping_id)

    def _get_display_price(self, product):
        # A product created from a promotion does not have a list_price.
        # The price_unit of a reward order line is computed by the promotion, so it can be used directly
        if self.is_reward_line:
            return self.price_unit
        return super()._get_display_price(product)

    # Invalidation of `coupon.program.order_count`
    # `test_program_rules_validity_dates_and_uses`,
    # Overriding modified is quite hardcore as you need to know how works the cache and the invalidation system,
    # but at least the below works and should be efficient.
    # Another possibility is to add on product.product a one2many to sale.order.line 'order_line_ids',
    # and then add the depends @api.depends('discount_line_product_id.order_line_ids'),
    # but I am not sure this will as efficient as the below.
    def modified(self, fnames, *args, **kwargs):
        super(PosOrderLine, self).modified(fnames, *args, **kwargs)
        if 'product_id' in fnames:
            Program = self.env['coupon.program'].sudo()
            field_order_count = Program._fields['order_count']
            programs = self.env.cache.get_records(Program, field_order_count)
            if programs:
                products = self.filtered('is_reward_line').mapped('product_id')
                for program in programs:
                    if program.discount_line_product_id in products:
                        self.env.cache.invalidate([(field_order_count, program.ids)])

    @api.depends('price_unit', 'discount')
    def _get_price_reduce(self):
        for line in self:
            line.price_reduce = line.price_unit * (1.0 - line.discount / 100.0)


    def get_code_product(self, product_id):
        product = self.env['product.product']