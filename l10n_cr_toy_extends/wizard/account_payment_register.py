# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    comission_bank_apply = fields.Boolean(string='Aplica comisión bancaria')
    comission_amount = fields.Monetary(string='Monto comisión', default=0.0)
    comission_expense_account_id = fields.Many2one('account.account',string='Cuenta para gasto')
    comission_amount_real = fields.Monetary('Monto real de pago', store=True, readonly=True, compute='compute_comission_amount_real')

    sale_order_ids = fields.Many2many('sale.order', string='Órdenes de venta')
    purchase_order_ids = fields.Many2many('purchase.order', string='Órdenes de compra')

    @api.depends('company_id', 'source_currency_id')
    def _compute_journal_id(self):
        super(AccountPaymentRegister, self)._compute_journal_id()
        for wizard in self:
            wizard.comission_expense_account_id = wizard.journal_id.account_expense_id

    @api.onchange('comission_bank_apply')
    def _change_comission_bank_apply(self):
        if not self.comission_bank_apply:
            self.comission_amount = 0.0
            #self.comission_expense_account_id = False

    @api.depends('amount','comission_amount')
    def compute_comission_amount_real(self):
        for wizard in self:
            if wizard.comission_bank_apply and not wizard.comission_amount < 0.0:
                amount_real = wizard.amount - wizard.comission_amount
                wizard.comission_amount_real = amount_real

    def _create_payments(self):
        self.ensure_one()
        batches = self._get_batches()
        edit_mode = self.can_edit_wizard and (len(batches[0]['lines']) == 1 or self.group_payment)

        to_reconcile = []
        if edit_mode:
            payment_vals = self._create_payment_vals_from_wizard()
            payment_vals_list = [payment_vals]
            #TODO: REDUCIR EL MONTO A PAGAR PAGO DE COMISIONES
            if self.comission_bank_apply and self.comission_amount > 0.0 and self.comission_expense_account_id:
                self._reduce_amount(payment_vals_list)
            to_reconcile.append(batches[0]['lines'])
        else:
            # Don't group payments: Create one batch per move.
            if not self.group_payment:
                new_batches = []
                for batch_result in batches:
                    for line in batch_result['lines']:
                        new_batches.append({
                            **batch_result,
                            'lines': line,
                        })
                batches = new_batches

            payment_vals_list = []
            for batch_result in batches:
                payment_vals_list.append(self._create_payment_vals_from_batch(batch_result))
                to_reconcile.append(batch_result['lines'])

        payments = self.env['account.payment'].create(payment_vals_list)

        # If payments are made using a currency different than the source one, ensure the balance match exactly in
        # order to fully paid the source journal items.
        # For example, suppose a new currency B having a rate 100:1 regarding the company currency A.
        # If you try to pay 12.15A using 0.12B, the computed balance will be 12.00A for the payment instead of 12.15A.
        if edit_mode:
            for payment, lines in zip(payments, to_reconcile):
                # Batches are made using the same currency so making 'lines.currency_id' is ok.
                if payment.currency_id != lines.currency_id:
                    liquidity_lines, counterpart_lines, writeoff_lines = payment._seek_for_lines()
                    source_balance = abs(sum(lines.mapped('amount_residual')))
                    payment_rate = liquidity_lines[0].amount_currency / liquidity_lines[0].balance
                    source_balance_converted = abs(source_balance) * payment_rate

                    # Translate the balance into the payment currency is order to be able to compare them.
                    # In case in both have the same value (12.15 * 0.01 ~= 0.12 in our example), it means the user
                    # attempt to fully paid the source lines and then, we need to manually fix them to get a perfect
                    # match.
                    payment_balance = abs(sum(counterpart_lines.mapped('balance')))
                    payment_amount_currency = abs(sum(counterpart_lines.mapped('amount_currency')))
                    if not payment.currency_id.is_zero(source_balance_converted - payment_amount_currency):
                        continue

                    delta_balance = source_balance - payment_balance

                    # Balance are already the same.
                    if self.company_currency_id.is_zero(delta_balance):
                        continue

                    # Fix the balance but make sure to peek the liquidity and counterpart lines first.
                    debit_lines = (liquidity_lines + counterpart_lines).filtered('debit')
                    credit_lines = (liquidity_lines + counterpart_lines).filtered('credit')

                    payment.move_id.write({'line_ids': [
                        (1, debit_lines[0].id, {'debit': debit_lines[0].debit + delta_balance}),
                        (1, credit_lines[0].id, {'credit': credit_lines[0].credit + delta_balance}),
                    ]})

        payments.action_post()

        domain = [('account_internal_type', 'in', ('receivable', 'payable')), ('reconciled', '=', False)]
        for payment, lines in zip(payments, to_reconcile):

            # When using the payment tokens, the payment could not be posted at this point (e.g. the transaction failed)
            # and then, we can't perform the reconciliation.
            if payment.state != 'posted':
                continue

            payment_lines = payment.line_ids.filtered_domain(domain)
            for account in payment_lines.account_id:
                (payment_lines + lines)\
                    .filtered_domain([('account_id', '=', account.id), ('reconciled', '=', False)])\
                    .reconcile()

        #TODO: CREACIOON DE ASIENTO CONTABLE PARA COMISION BANCARIA
        self._create_move_bank_comission(payments)
        return payments

    def _create_move_bank_comission(self, payments):
        if self.comission_bank_apply:
            account_journal_in_move = payments.line_ids.mapped('account_id').filtered(lambda a: a.user_type_id.type not in ('receivable', 'payable'))

            line_ids = [(0, 0, {
                'account_id': self.journal_id.payment_credit_account_id.id,
                'partner_id': self.partner_id.id,
                'credit': self.comission_amount,
            }), (0, 0, {
                'account_id': self.comission_expense_account_id.id,
                'partner_id': self.partner_id.id,
                'debit': self.comission_amount,
            })]

            vals = {
                'date':  self.payment_date,
                'company_id': self.env.company.id,
                'journal_id':self.journal_id.id,
                'ref': payments.move_id.name,
                'narration': 'Movimiento de comisión bancaria',
                'line_ids': line_ids
            }
            move_id = self.env['account.move'].sudo().create(vals)
            if move_id:
                print('CREADO => Asiento contable para comision bancaria')
                move_id.action_post()
            else:
                print('NO CREADO => Asiento contable para comision bancaria')
            _logger.info(move_id)


    def _reduce_amount(self,payment):
        payment[0]['amount'] = self.comission_amount_real

    @api.model
    def default_get(self, fields_list):
        res = super(AccountPaymentRegister, self).default_get(fields_list)
        if 'line_ids' in res:
            lines = self.env['account.move.line'].sudo().browse(res['line_ids'][0][2])
            if lines:
                inv_ids = lines.mapped('move_id')
                if inv_ids:
                    sale_order_ids = self.env['sale.order'].sudo().search([('invoice_ids','in',inv_ids.ids)])
                    if sale_order_ids:
                        res['sale_order_ids'] = [(6,0,sale_order_ids.ids)]

                    purchase_order_ids = self.env['purchase.order'].sudo().search([('invoice_ids', 'in', inv_ids.ids)])
                    if purchase_order_ids:
                        res['purchase_order_ids'] = [(6, 0, purchase_order_ids.ids)]

        return res

    def _create_payment_vals_from_batch(self, batch_result):
        res = super(AccountPaymentRegister, self)._create_payment_vals_from_batch(batch_result)
        if self.sale_order_ids:
            res['sale_order_ids'] = [(6, 0, self.sale_order_ids.ids)]

        if self.purchase_order_ids:
            res['purchase_order_ids'] = [(6, 0, self.purchase_order_ids.ids)]

        return res

    def _create_payment_vals_from_wizard(self):
        payment_vals = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard()
        if self.sale_order_ids:
            payment_vals['sale_order_ids'] = [(6, 0, self.sale_order_ids.ids)]

        if self.purchase_order_ids:
            payment_vals['purchase_order_ids'] = [(6, 0, self.purchase_order_ids.ids)]
        return payment_vals