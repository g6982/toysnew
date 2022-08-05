# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    active_create_invoice = fields.Boolean(string='Crear factura', copy=False)

    @api.constrains('active_create_invoice')
    def _check_active_create_invoice(self):
        if self.code == 'internal' and self.active_create_invoice:
            raise ValidationError(_("Solo puede activar la creación de facturas para tipo: entrada y recepción."))

    @api.onchange('code')
    def _onchange_picking_code(self):
        res = super(StockPickingType, self)._onchange_picking_code()
        if self.code == 'internal':
            self.active_create_invoice = False
        return res