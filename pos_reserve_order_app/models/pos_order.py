# -*- coding: utf-8 -*-

from itertools import groupby
from datetime import datetime, timedelta

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def _payment_fields(self, order, ui_paymentline):
        return {
            'amount': ui_paymentline['amount'] or 0.0,
            'payment_date': ui_paymentline['name'],
            'payment_method_id': ui_paymentline['payment_method_id'],
            'card_type': ui_paymentline.get('card_type'),
            'cardholder_name': ui_paymentline.get('cardholder_name'),
            'transaction_id': ui_paymentline.get('transaction_id'),
            'payment_status': ui_paymentline.get('payment_status'),
            'pos_order_id': order.id,
            'session_id': 1
        }

    def _create_order_picking(self):
        self.ensure_one()
        if not self.session_id.update_stock_at_closing or (self.company_id.anglo_saxon_accounting and self.to_invoice):
            picking_type = self.config_id.picking_type_id
            if self.state == 'reserved':
                if self.config_id.enable_reservation and not self.config_id.reservation_location:
                    raise UserError(_('El monto a pagar no puede ser mayor al monto adeudado ! '))
                destination_id = self.config_id.reservation_location.id
            elif self.partner_id.property_stock_customer:
                destination_id = self.partner_id.property_stock_customer.id
            elif not picking_type or not picking_type.default_location_dest_id:
                destination_id = self.env['stock.warehouse']._get_partner_locations()[0].id
            else:
                destination_id = picking_type.default_location_dest_id.id

            pickings = self.env['stock.picking']._create_picking_from_pos_order_lines(destination_id, self.lines, picking_type, self.partner_id)
            pickings.write({'pos_session_id': self.session_id.id, 'pos_order_id': self.id, 'origin': self.name})


    def get_method_last_paid(self):
        if self:
            for paid in self.payment_ids:
                a=paid
            pago = self.payment_ids[0]
            return pago
