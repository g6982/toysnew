# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import Warning


class AccountAccount(models.Model):
    _inherit = "account.account"

    special_cash_pos = fields.Boolean('Especialmente para efectivo en POS')

    @api.model
    def get_accounts_in(self,ids):
        res = []
        if ids:
            accounts_id = self.env['account.account'].sudo().search([('id','in',ids)])
            for a in accounts_id:
                json = {
                    'id': a.id,
                    'name': a.name,
                    'code': a.code
                }
                res.append(json)
            return res
        else:
            return res

