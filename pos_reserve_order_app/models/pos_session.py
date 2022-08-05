# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.http import request
from collections import defaultdict


class PosSessionInherit(models.Model):
    _inherit = 'pos.session'

    order_reserved_ids = fields.Many2many('pos.order', 'session_order_reserverd', 'session_id', 'order_id')
    @api.depends('order_ids.payment_ids.amount')
    def _compute_total_payments_amount(self):
        super(PosSessionInherit, self)._compute_total_payments_amount()
        for session in self:
            total_payments_amount = session.total_payments_amount
            session.total_payments_amount = self._aditional_payments_reserved(session)

    @api.depends('payment_method_ids', 'order_ids', 'cash_register_balance_start', 'cash_register_id')
    def _compute_cash_balance(self):
        for session in self:
            #cash_payment_method = session.payment_method_ids.filtered('is_cash_count')[:1]
            cash_payment_method = session.payment_method_ids.filtered('is_cash_count')
            if cash_payment_method:
                #total_cash_payment = sum(session.order_ids.mapped('payment_ids').filtered(lambda payment: payment.payment_method_id == cash_payment_method).mapped('amount')) #TODO:ORIGIN
                #total_cash_payment = sum(self._payments_reserved(session).filtered(lambda payment: payment.payment_method_id == cash_payment_method).mapped('amount'))
                total_cash_payment = sum(self._payments_reserved(session).filtered(lambda payment: payment.payment_method_id.id in cash_payment_method.ids).mapped('amount'))
                session.cash_register_total_entry_encoding = session.cash_register_id.total_entry_encoding + (0.0 if session.state == 'closed' else total_cash_payment)
                session.cash_register_balance_end = session.cash_register_balance_start + session.cash_register_total_entry_encoding
                session.cash_register_difference = session.cash_register_balance_end_real - session.cash_register_balance_end
            else:
                session.cash_register_total_entry_encoding = 0.0
                session.cash_register_balance_end = 0.0
                session.cash_register_difference = 0.0

    def _payments_reserved(self,session):
        payments_reserved = self.env['pos.payment'].search([('session_id', '=', session.id)])
        return payments_reserved

    def _aditional_payments_reserved(self,session):
        total_payments_for_session = 0.0
        #payments = self._payments_reserved(session) - session.order_ids.mapped('payment_ids')
        payments = self._payments_reserved(session)
        total_payments_for_session = sum(payments.mapped('amount'))
        return total_payments_for_session

    def _validate_session(self):
        self.ensure_one()
        #if self.order_ids or self.statement_ids.line_ids or self.order_reserved_ids: TODO: ORIGINAL
        if self.order_ids or self.statement_ids.line_ids or self.order_reserved_ids: #TODO: MODIFICADO AGREGANDO "order_reserved_ids"
            self.cash_real_transaction = self.cash_register_total_entry_encoding
            self.cash_real_expected = self.cash_register_balance_end
            self.cash_real_difference = self.cash_register_difference
            if self.state == 'closed':
                raise UserError(_('This session is already closed.'))
            self._check_if_no_draft_orders()
            if self.update_stock_at_closing:
                self._create_picking_at_end_of_session()
            # Users without any accounting rights won't be able to create the journal entry. If this
            # case, switch to sudo for creation and posting.
            try:
                self.with_company(self.company_id)._create_account_move()
            except AccessError as e:
                if self.user_has_groups('point_of_sale.group_pos_user'):
                    self.sudo().with_company(self.company_id)._create_account_move()
                else:
                    raise e
            if self.move_id.line_ids:
                # Set the uninvoiced orders' state to 'done'
                self.env['pos.order'].search([('session_id', '=', self.id), ('state', '=', 'paid')]).write({'state': 'done'})
            else:
                self.move_id.unlink()
        self.write({'state': 'closed'})
        return {
            'type': 'ir.actions.client',
            'name': 'Point of Sale Menu',
            'tag': 'reload',
            'params': {'menu_id': self.env.ref('point_of_sale.menu_point_root').id},
        }

