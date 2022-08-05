# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import Counter, defaultdict

from odoo import _, api, fields, tools, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import OrderedSet
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.tools.misc import clean_context, format_date, OrderedSet

class StockMoveLine(models.Model):
    _inherit = "stock.move"

    note_toys = fields.Text('Nota')

    def _action_confirm(self, merge=True, merge_into=False):
        """ Confirms stock move or put it in waiting if it's linked to another move.
        :param: merge: According to this boolean, a newly confirmed move will be merged
        in another move of the same picking sharing its characteristics.
        """
        move_create_proc = self.env['stock.move']
        move_to_confirm = self.env['stock.move']
        move_waiting = self.env['stock.move']

        to_assign = {}
        for move in self:
            move._assign_notes()  # Asignar notas
            if move.state != 'draft':
                continue
            # if the move is preceeded, then it's waiting (if preceeding move is done, then action_assign has been called already and its state is already available)
            if move.move_orig_ids:
                move_waiting |= move
            else:
                if move.procure_method == 'make_to_order':
                    move_create_proc |= move
                else:
                    move_to_confirm |= move
            if move._should_be_assigned():
                key = (move.group_id.id, move.location_id.id, move.location_dest_id.id)
                if key not in to_assign:
                    to_assign[key] = self.env['stock.move']
                to_assign[key] |= move


        # create procurements for make to order moves
        procurement_requests = []
        for move in move_create_proc:
            values = move._prepare_procurement_values()
            origin = (move.group_id and move.group_id.name or (move.origin or move.picking_id.name or "/"))
            procurement_requests.append(self.env['procurement.group'].Procurement(
                move.product_id, move.product_uom_qty, move.product_uom,
                move.location_id, move.rule_id and move.rule_id.name or "/",
                origin, move.company_id, values))

        self.env['procurement.group'].run(procurement_requests, raise_user_error=not self.env.context.get('from_orderpoint'))

        move_to_confirm.write({'state': 'confirmed'})
        (move_waiting | move_create_proc).write({'state': 'waiting'})
        # assign picking in batch for all confirmed move that share the same details
        for moves in to_assign.values():
            moves.with_context(clean_context(
                moves.env.context))._assign_picking()
        self._push_apply()
        self._check_company()
        moves = self
        if merge:
            moves = self._merge_moves(merge_into=merge_into)
        # call `_action_assign` on every confirmed move which location_id bypasses the reservation
        moves.filtered(lambda move: not move.picking_id.immediate_transfer and move._should_bypass_reservation() and move.state == 'confirmed')._action_assign()
        return moves



    def _assign_notes(self):
        note_toys = False
        if self.sale_line_id:
            if self.sale_line_id.note_toys:
                note_toys = self.sale_line_id.note_toys
        elif self.move_dest_ids:
            if self.move_dest_ids.note_toys:
                note_toys = self.move_dest_ids.note_toys

        self.note_toys = note_toys


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    result_package_toys_id = fields.Many2one('stock.quant.package', compute='_compute_result_package_toys_')
    contact_id = fields.Many2one('res.partner',related='picking_id.partner_id', string='Contacto')
    qty_available = fields.Float(string='A mano', store=True, compute='_compute_qty_available',digits='Product Unit of Measure',)

    transfer_id = fields.Many2one('stock.picking', string='Transferencia', compute='_compute_reference')
    sale_order_id = fields.Many2one('sale.order', string='Orden de venta', compute='_compute_reference')
    purchase_order_id = fields.Many2one('purchase.order', string='Orden de compra', compute='_compute_reference')
    pos_order_id = fields.Many2one('pos.order', string='Pedido POS', compute='_compute_reference')

    note_toys = fields.Text('Nota', related='move_id.note_toys')

    @api.depends('package_id')
    def _compute_result_package_toys_(self):
        for record in self:
            record.result_package_toys_id = record.package_id
            record.result_package_id = record.package_id

    @api.depends('product_id')
    def _compute_qty_available(self):
        for record in self:
            record.qty_available = record.product_id.qty_available

    @api.depends('reference')
    def _compute_reference(self):
        for record in self:
            transfer_id = False
            sale_order_id = False
            purchase_order_id = False
            pos_order_id = False
            if record.reference:
                transfer_id = self.env['stock.picking'].sudo().search([('name', '=', record.reference)])
                #pos_order_id
                if transfer_id:
                    if transfer_id.pos_order_id:
                        pos_order_id = transfer_id.pos_order_id
                    elif transfer_id.origin:
                        sale_order_id = self.env['sale.order'].sudo().search([('name', '=', transfer_id.origin)], limit=1)

                    elif not sale_order_id and transfer_id.origin:
                        purchase_order_id = self.env['purchase.order'].sudo().search([('name', '=', transfer_id.origin)], limit=1)

            record.transfer_id = transfer_id
            record.sale_order_id = sale_order_id
            record.purchase_order_id = purchase_order_id
            record.pos_order_id = pos_order_id