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

class SaleOrderImportWizard(models.TransientModel):
    _name = 'sale.order.import.wizard'
    _description = 'Importacion para actualización de órdenes de venta'

    file = fields.Binary(string="Subir archivo (.xlsx)", required=False)
    file_name = fields.Char(string="Nombre del archivo")
    company_id = fields.Many2one('res.company', string=u'Compañia', default=lambda self: self.env.user.company_id)
    logs = fields.Text('Advertencias')


    def import_file(self):
        """ function to import product details from csv and xlsx file """
        try:
            fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.file))
            fp.seek(0)
            workbook = xlrd.open_workbook(fp.name)
            sheet = workbook.sheet_by_index(0)
        except:
            raise Warning(_("¡Elija un archivo correcto!"))

        return self._process_sheet(sheet)


    def _process_sheet(self,sheet):
        desde = 1
        hasta = sheet.nrows
        orders_errors = []

        sale_order_line= self.env['sale.order.line']

        pos = 1
        for i in range(desde, hasta):
            pos += 1
            code_order = sheet.cell(i,0).value
            code_product= sheet.cell(i,1).value
            quantity = sheet.cell(i,2).value
            note_toys = sheet.cell(i,3).value

            order = self.env['sale.order'].sudo().search([('name','=',code_order)])
            product = self.env['product.product'].sudo().search([('default_code', '=', code_product)])

            if not order:
                orders_errors.append('Linea:' + str(pos) + ' - el pedido : ' + str(code_order) + ' no fue encontrado.')
            elif not product:
                orders_errors.append('Linea:' + str(pos) + ' - el producto : ' + str(code_product) + ' no fue encontrado.')
            elif order and product:
                if order.state not in ('draft','sent'):
                    orders_errors.append('Linea:' + str(pos) + ' - el pedido : ' + str(code_order) + ' esta en estado : ' + str(order.state))
                else:
                    sw = 0
                    for line in order.order_line:
                        if line.product_id.default_code == code_product:
                            sw = 1
                            line.product_uom_qty = quantity
                            break

                    if sw == 0:
                        sol = sale_order_line.create({
                            'product_id': product.id,
                            'name': product.name,
                            'qty_available': product.qty_available,
                            'product_uom_qty': quantity,
                            'order_id': order.id,
                            'note_toys': note_toys
                        })
                        if sol:
                            sol.sudo()._compute_qty_reserved()

            else:
                orders_errors.append('Linea:' + str(pos) + ' - ERROR NO CONOCIDO')

        self.logs = 'good'
        if orders_errors:
            message = ''
            for e in orders_errors:
                message += '*' + e + '\n'

            self.logs = message


        return {
            u'name': u'Resultado del proceso de pedidos',
            u'type': u'ir.actions.act_window',
            u'view_mode': u'form',
            u'target': u'new',
            u'res_model': u'sale.order.import.wizard',
            u'res_id': self.id
        }



    def download_file_xlx(self):
        self.ensure_one()
        url = f'/l10n_cr_toy_extends/static/xlsx/CARGA_PRODUCTOS_EN_PEDIDOS.xlsx'
        return {
            'name': _("Excel"),
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }



    def link_quotations_action(self):
        """ Return the action used to display orders when returning from customer portal. """
        # self.ensure_one()
        # return self.env.ref('sale.action_quotations_with_onboarding')
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_quotations_with_onboarding")
        return action

