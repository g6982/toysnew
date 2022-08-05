# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.osv import expression
class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    def _seek_for_lines(self):

        liquidity_lines = self.env['account.move.line']
        suspense_lines = self.env['account.move.line']
        other_lines = self.env['account.move.line']

        for line in self.move_id.line_ids:
            if line.account_id == self.journal_id.default_account_id:
                liquidity_lines += line
            elif line.account_id == self.journal_id.suspense_account_id:
                suspense_lines += line
            else:
                other_lines += line

        #Nuevo para cuenta especial de caja en POS.
        if not suspense_lines:
            for line in self.move_id.line_ids:
                if line.account_id.special_cash_pos:
                    suspense_lines += line

        return liquidity_lines, suspense_lines, other_lines
