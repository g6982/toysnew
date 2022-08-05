# -*- coding: utf-8 -*-
import logging

from datetime import datetime, date
import base64
from odoo.exceptions import UserError, ValidationError

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare
import pytz


class AccountMoveCloseWizard(models.TransientModel):
    _name = "account.move.close.wizard"
    _description = "Generar cierres de caja"

    def _get_horario_cr(self):
        now_utc = datetime.now(pytz.timezone("UTC"))
        now_cr = now_utc.astimezone(pytz.timezone("America/Costa_Rica"))

        return now_cr.date()

    company_id = fields.Many2one('res.company', string=u'Compañia', default=lambda self: self.env.user.company_id)
    date_from = fields.Date('Fecha de inicio', required=True, default=_get_horario_cr)
    date_to = fields.Date('Fecha de fin', required=True, default=_get_horario_cr)
    branch_ids = fields.Many2many('res.branch',string='Ramas', required=True)
    payment_term_ids = fields.Many2many('pos.payment.method',string='Formas de pago')
    type = fields.Selection([('yop','Seleccionar mis formas de pago.'),('nop','Que no necesariamente tengan formas de pago relacionadas.')],
                            string='Necesito ', default='yop')

    @api.constrains('date_from', 'date_to')
    def _check_date(self):
        if self.date_to > self.date_from:
            raise ValidationError(_('La fecha de inicio debe ser menor a la fecha de fin.'))

    @api.onchange('type')
    def _onchange_type(self):
        if self.type=='nop':
            self.payment_term_ids = False

    def generate_moves_closes(self):

        branch_ids = self.branch_ids
        term_paid_ids = self.payment_term_ids
        date_from = self.date_from
        date_to = self.date_to
        event_cron_id = self.env.ref('branch.ir_cron_move_close_branch')
        self.env['res.branch'].sudo()._account_move_close_branch(branch_ids, term_paid_ids, date_from, date_to, event_cron_id, False)