# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools.float_utils import float_is_zero
from odoo.exceptions import UserError, ValidationError


class StockLocatin(models.Model):
    _inherit = 'stock.location'

    is_out = fields.Boolean(string='¿Es una ubicación de salida?', default=False, copy=False)


class StockPiking(models.Model):
    _inherit = 'stock.picking'

    carrier_id = fields.Many2one("delivery.carrier", string="Método entrega")

    is_out = fields.Boolean(related='location_id.is_out', copy=False)
    user_responsible = fields.Many2one('res.users', string='Responsable', copy=False)

    picking_origin_ids = fields.Many2many('stock.picking', 'rel_stockpicking_merge_ids', 'sp_id', 'sp_merge_id', string='Picking relacionados', copy=False)
    picking_origin_counts = fields.Integer(compute='_compute_picking_related', copy=False)

    operation_code = fields.Selection(related='picking_type_id.code', store=True, readonly=True, copy=False)  # Del módulo stock_move_invoice
    active_create_invoice = fields.Boolean(string='Crear factura', related='picking_type_id.active_create_invoice', copy=False)

    last_state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),

    ])

    state = fields.Selection(selection_add=[
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('to_be_approved', 'Esperando aprobación'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),

    ],
        ondelete={
            'draft': 'cascade',
            'waiting': 'cascade',
            'confirmed': 'cascade',
            'assigned': 'cascade',
            'to_be_approved': 'cascade',
            'done': 'cascade',
            'cancel': 'cascade'}, tracking=True)

    def show_picking_backorder_wizard(self):

        product_ids = self.move_line_ids_without_package.mapped('product_id')
        categ_ids = product_ids.mapped('categ_id').ids

        location_ids = self.move_line_ids_without_package.mapped('location_id')

        total_lines = len(self.move_line_ids_without_package)
        ctx = dict(
            default_picking_id=self.id,
            default_categ_defult_ids=categ_ids,
            default_categ_ids=categ_ids,
            default_location_default_ids=location_ids.ids,
            default_location_ids=location_ids.ids,
            default_total_lines=total_lines,
            default_lines_ids=self.move_line_ids_without_package.ids,
        )

        return {
            'name': _('Backorder'),
            'res_model': 'stock.picking.update.wizard',
            'view_mode': 'form',
            'context': ctx,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    # sobreescritura de módulo stock_move_invoice
    def create_invoice(self):
        """This is the function for creating customer invoice
        from the picking"""
        for picking_id in self:
            current_user = self.env.uid
            if picking_id.picking_type_id.code == 'outgoing':
                customer_journal_id = picking_id.env['ir.config_parameter'].sudo().get_param(
                    'stock_move_invoice.customer_journal_id') or False
                if not customer_journal_id:
                    raise UserError(_("Please configure the journal from settings"))
                invoice_line_list = []
                line_zero = picking_id.move_ids_without_package[0]
                for move_ids_without_package in picking_id.move_ids_without_package:
                    # Mejora 2022-04-19
                    if move_ids_without_package.sale_line_id:
                        line = move_ids_without_package.sale_line_id
                        vals = (0, 0, {
                            'name': line.name,
                            'product_id': line.product_id.id,
                            'price_unit': line.price_unit,
                            'account_id': line.product_id.property_account_income_id.id if line.product_id.property_account_income_id
                            else line.product_id.categ_id.property_account_income_categ_id.id,
                            'tax_ids': [(6, 0, line.tax_id.ids)],
                            'quantity': line.product_uom_qty,
                            'discount': line.discount  # New 2021-10-21

                        })
                        invoice_line_list.append(vals)
                # for move_ids_without_package in picking_id.move_ids_without_package:
                #     vals = (0, 0, {
                #         'name': move_ids_without_package.description_picking,
                #         'product_id': move_ids_without_package.product_id.id,
                #         'price_unit': move_ids_without_package.product_id.lst_price,
                #         'account_id': move_ids_without_package.product_id.property_account_income_id.id if move_ids_without_package.product_id.property_account_income_id
                #         else move_ids_without_package.product_id.categ_id.property_account_income_categ_id.id,
                #         'tax_ids': [(6, 0, move_ids_without_package.sale_line_id.tax_id.ids)],
                #         'quantity': move_ids_without_package.quantity_done,
                #         'discount': move_ids_without_package.sale_line_id.discount  # New 2021-10-21
                #
                #     })
                #     invoice_line_list.append(vals)

                invoice = picking_id.env['account.move'].create({
                    'move_type': 'out_invoice',
                    'invoice_origin': picking_id.name,
                    'invoice_user_id': current_user,
                    'narration': picking_id.name,
                    'partner_id': picking_id.partner_id.id,
                    'currency_id': line_zero.sale_line_id.order_id.pricelist_id.currency_id.id,
                    'journal_id': int(customer_journal_id),
                    'payment_reference': picking_id.name,
                    'picking_id': picking_id.id,
                    'invoice_line_ids': invoice_line_list,
                    'discount_partner': line_zero.sale_line_id.order_id.discount_partner,
                    'apply_discount_global': line_zero.sale_line_id.order_id.apply_discount_global,
                    'percentage_discount_global': line_zero.sale_line_id.order_id.percentage_discount_global,
                })
                return invoice

    def create_bill(self):
        if self.picking_type_id.code == 'incoming':
            return super(StockPiking, self).create_bill()
        else:
            raise ValidationError(_("Solo aplica para transferencias de tipo entrada."))

    def action_view_picking_related(self):
        if self.picking_origin_ids:
            result = {
                'name': _('Picking creados'),
                'type': 'ir.actions.act_window',
                'res_model': 'stock.picking',
                'view_mode': 'list',
                'domain': [('id', 'in', self.picking_origin_ids.ids)],
                'views': [(self.env.ref('stock.vpicktree').id, 'list'), (self.env.ref('stock.view_picking_form').id, 'form')]
            }
            return result

    def _compute_picking_related(self):
        for record in self:
            record.picking_origin_counts = len(record.picking_origin_ids)


    def button_validate(self):
        company = self.company_id
        if company.inventory_approve and self.state not in ('to_be_approved','done'):
            self.last_state = self.state
            self.state = 'to_be_approved'
        elif self.state == 'to_be_approved':
            self.state = self.last_state
            return super(StockPiking, self).button_validate()
        else:
            #self.state = self.last_state if self.last_state
            return super(StockPiking, self).button_validate()

    def stock_picking_approve(self):
        return super(StockPiking, self).button_validate()


    #@overrite
    @api.model
    def _create_picking_from_pos_order_lines(self, location_dest_id, lines, picking_type, partner=False):
        """We'll create some picking based on order_lines"""

        pickings = self.env['stock.picking']
        stockable_lines = lines.filtered(
            lambda l: l.product_id.type in ['product', 'consu'] and not float_is_zero(l.qty,
                                                                                      precision_rounding=l.product_id.uom_id.rounding))
        if not stockable_lines:
            return pickings
        positive_lines = stockable_lines.filtered(lambda l: l.qty > 0)
        negative_lines = stockable_lines - positive_lines

        if positive_lines:
            pos_order = positive_lines[0].order_id
            location_id = pos_order.location_id.id
            if 'is_reserved' in pos_order and pos_order.state == 'paid':
                if pos_order.is_reserved:
                    location_id = pos_order.config_id.reservation_location.id
            vals = self._prepare_picking_vals(partner, picking_type, location_id, location_dest_id)
            positive_picking = self.env['stock.picking'].create(vals)
            positive_picking._create_move_from_pos_order_lines(positive_lines)
            try:
                with self.env.cr.savepoint():
                    positive_picking._action_done()
            except (UserError, ValidationError):
                pass

            pickings |= positive_picking
        if negative_lines:
            if picking_type.return_picking_type_id:
                return_picking_type = picking_type.return_picking_type_id
                return_location_id = return_picking_type.default_location_dest_id.id
            else:
                return_picking_type = picking_type
                return_location_id = picking_type.default_location_src_id.id
                # Todo:Nuevo >> Agregando ubicacion de retorno de productos
                order_id = negative_lines.order_id
                #if order_id.return_order_ref and picking_type.default_location_refund_id: ANTES
                if order_id.return_order_id and picking_type.default_location_refund_id: #AHORA
                    return_location_id = picking_type.default_location_refund_id.id

            vals = self._prepare_picking_vals(partner, return_picking_type, location_dest_id, return_location_id)
            negative_picking = self.env['stock.picking'].create(vals)
            negative_picking._create_move_from_pos_order_lines(negative_lines)
            try:
                with self.env.cr.savepoint():
                    negative_picking._action_done()
            except (UserError, ValidationError):
                pass
            pickings |= negative_picking
        return pickings