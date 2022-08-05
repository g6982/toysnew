# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round
from odoo.exceptions import AccessError, UserError, ValidationError

class PurchsaeOrderFollowStateIn(models.Model):
    _name = 'purchase.order.follow.state.in'
    _description = "Estado de ingreso a almacén"
    _order = 'name'

    name = fields.Char('Nombre')

    _sql_constraints = [('name_uniq', 'unique (name)', "El nombre del estado ya existe !"),]

class PurchsaeOrderFollow(models.Model):
    _name = 'purchase.order.follow'
    _inherit = ['mail.thread']
    _description = "Seguimiento en órdenes de compra"
    _order = 'id desc'

    purchase_id = fields.Many2one('purchase.order', string=u'Órden de compra', copy=False)
    date_dispatch = fields.Date(string='Fecha de despacho', copy=False)
    date_proforma = fields.Date(string='Fecha de proforma', copy=False)
    bl = fields.Char(string='BL', copy=False)
    container = fields.Char(string='Contenedor', copy=False)
    date_etd = fields.Date(string='ETD', copy=False) #Fecha salida de origen
    date_eta = fields.Date(string='ETA', copy=False) #Fecha llegada estimada
    date_ata = fields.Date(string='ATA', copy=False) #FEcha llegada confirmada
    location_id = fields.Many2one('stock.location', string=u'Almacén', copy=False)
    date_in_location = fields.Date(string='Fecha ingreso a almacén', copy=False)
    date_now = fields.Date(string='Fecha actual',  default=lambda self: fields.Date.context_today(self), copy=False)
    days_in_location = fields.Integer(string='Dias en almacén', copy=False, compute='_compute_days_in_location', store=True)
    move = fields.Char(string='Movimiento', copy=False)
    state_in = fields.Many2one('purchase.order.follow.state.in',string='Estado de ingreso', copy=False)
    dua = fields.Char(string='DUA', copy=False)
    date_dua = fields.Date(string='Fecha dua', copy=False)
    traffic_light_color = fields.Selection([('green','Verde'),('yellow','Amarillo'),('red','Rojo')], string=u'Semáforo', copy=False)
    date_out_of_stock = fields.Date('Fecha desalmacenado', copy=False)

    @api.depends('date_now','date_in_location')
    def _compute_days_in_location(self):
        for record in self:
            days = 0
            if record.date_in_location and record.date_now:
                days = (record.date_now - record.date_in_location).days

            record.days_in_location = days




