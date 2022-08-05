# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round
from odoo.exceptions import AccessError, UserError, ValidationError

class ContainerType(models.Model):
    _name = 'container.type'
    _inherit = ['mail.thread']
    _description = "Tipo de contenedor"
    _order = 'id desc'

    name = fields.Char(string=u'Código')
    description = fields.Char(string='Nombre')
    space = fields.Float(string='Cubicaje max.', default=0.0)
    remaining_space = fields.Float(string='Espacio restante.', compute='_compute_remaining_space', default=0.0)
    order_ids = fields.One2many('purchase.order', 'type_container', string='Órdenes de compra')

    @api.constrains('remaining_space')
    def _check_remaining_space(self):
        for record in self:
            if record.remaining_space > record.space:
                raise ValidationError(_('No puede exceder el espacio del contenedor'))

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} ({})".format(record.description, record.name or '')))
        return result

    @api.model
    def create(self, vals):
        res = super(ContainerType, self).create(vals)
        res.description = res.name
        seq_name = self.env.ref('l10n_cr_toy_extends.ir_sequence_container').next_by_id()
        res.name = seq_name
        return res

    @api.depends('order_ids','order_ids.state','order_ids.metro_cubico', 'space')
    def _compute_remaining_space(self):
        for record in self:
            total = 0.0
            if record.order_ids:
                orders_valid = record.order_ids.filtered(lambda o: o.state != 'cancel')
                if orders_valid:
                    total = sum(r.metro_cubico for r in orders_valid)
            record.remaining_space = record.space - total




