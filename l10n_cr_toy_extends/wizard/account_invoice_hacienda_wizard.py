# -*- coding: utf-8 -*-

import tempfile
import binascii
import requests
import base64
import certifi
import urllib3
import xlrd
from odoo.exceptions import Warning
from odoo import models, fields, _

class AccountInvoiceHaciendaWizard(models.TransientModel):
    _name = 'account.invoice.hacienda.wizard'
    _description = 'Factura a hacienda'

    rate = fields.Float(string='Tipo de cambio')
    currency_id = fields.Many2one('res.currency', string='Moneda')
    order_id = fields.Many2one('purchase.order', string='Orden de compra')
    change_is = fields.Boolean('Es un cambio')


    def process(self):
        return self.order_id.create_invoice_to_hacienda(self.change_is, self.rate)