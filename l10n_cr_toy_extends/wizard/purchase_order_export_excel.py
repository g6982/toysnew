# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from io import BytesIO
import base64
from datetime import datetime
import xlsxwriter
from .. import excel

STATE = [('purchase_order','Pedido de compra'),('purchase_proforma','Presupuesto')]

class PurchaseOrderExportExcel(models.TransientModel):
    _name = 'purchase.order.export.excel'
    _description = 'Purchase order export excel'

    order_id = fields.Many2one('purchase.order',string='Orden de compra',store=True, required=True, readonly=True)
    type = fields.Selection(selection=STATE, string="Imprimir", default='purchase_order', required=True)

    xls_filename = fields.Char(u'Nombre de fichero')
    xls_file = fields.Binary(u'Descargar reporte', readonly=True)

    def process(self):
        xls = BytesIO()
        workbook = xlsxwriter.Workbook(xls, {'in_memory': True})

        if self.type == 'purchase_order':
            excel.purchase_order._body_data(self,xls, workbook)
        else:
            excel.proforma_order._body_data(self, xls, workbook)

        workbook.close()
        xls.seek(0)
        return xls.getvalue()

    def excel_report(self):
        for rpt in self:
            if self.type == 'purchase_order':
                rec_name = 'PURCHASE_ORDER'
            else:
                rec_name = 'PURCHASE_PROFORMA'
            name = datetime.now().strftime("%Y%m%d%H%M%S")
            rpt.write(dict(
                xls_filename=rec_name+ '_' + name + '.xlsx',
                xls_file=base64.b64encode(self.process()),
            ))
            return {
                u'name': u'Archivo generado',
                u'type': u'ir.actions.act_window',
                u'view_type': u'form',
                u'view_mode': u'form',
                u'target': u'new',
                u'res_model': u'purchase.order.export.excel',
                u'res_id': rpt.id
            }

