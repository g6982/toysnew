# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import Warning


class AccountAccount(models.Model):
    _inherit = "account.account"

    active_comission = fields.Boolean(string='Activar comisiones', default=False)
    comission_bank_account = fields.Many2one('account.account',string='Cuenta comisión bancaria')
    comission_bank = fields.Float(string=u'Comisión Bancaria %', default=0.0)
    retention_isr_account = fields.Many2one('account.account',string='Cuenta retención isr')
    retention_isr = fields.Float(string=u'Retención ISR %', default=0.0)
    retention_iva_account = fields.Many2one('account.account',string='Cuenta retención iva')
    retention_iva = fields.Float(string=u'Retención IVA %', default=0.0)
    account_bank_id = fields.Many2one('account.account',string='Cuenta bancaria destino')

    @api.constrains('active_comission')
    def _check_active_comission(self):
        if self.active_comission:
            if not self.account_bank_id:
                raise Warning(_("Al activar el check de comisiones debe seleccionar la cuenta bancaria de destino"))
            if not self.comission_bank_account and not self.retention_isr_account and not self.retention_iva_account:
                raise Warning(_("Al activar el check de comisiones debe seleccionar al menos una cuenta de comisión"))

            if self.comission_bank_account and (not self.comission_bank or self.comission_bank < 0.0):
                raise Warning(_("Al seleccionar la cuenta para comisión bancaria, el monto de la comisión debe ser positivo"))

            if self.retention_isr_account and (not self.retention_isr or self.retention_isr < 0.0):
                raise Warning(_("Al seleccionar la cuenta para retención ISR, el monto de la comisión debe ser positivo"))

            if self.retention_iva_account and (not self.retention_iva or self.retention_iva < 0.0):
                raise Warning(_("Al seleccionar la cuenta para retención IVA, el monto de la comisión debe ser positivo"))


