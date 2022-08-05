from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp


class YWTInternalStockTransferLine(models.Model):
    _inherit = 'ywt.internal.stock.transfer.line'

    free_qty = fields.Float(string="Disponible real", compute='_compute_free_qty')

    @api.depends('product_id')
    def _compute_free_qty(self):
        for record in self:
            record.free_qty = record.product_id.free_qty




