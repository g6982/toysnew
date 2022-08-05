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

class InternalTransferImportWizard(models.TransientModel):
    _name = 'internal.transfer.import.wizard'
    _description = 'Importación de Transferencias Internas'

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

        internal_transfer = self.env['ywt.internal.stock.transfer'].sudo()

        groups = []
        pos = 1
        for i in range(desde, hasta):
            pos += 1
            warehouse_origin = sheet.cell(i,0).value
            warehouse_destiny = sheet.cell(i,1).value
            location_origin = sheet.cell(i,2).value
            location_destiny = sheet.cell(i,3).value
            code_product = sheet.cell(i,4).value
            quantity = sheet.cell(i,5).value


            product = self.env['product.product'].sudo().search([('default_code', '=', code_product)],limit=1)
            warehouse_from = self.env['stock.warehouse'].sudo().search([('name', '=ilike', warehouse_origin + '%')],limit=1)
            warehouse_to = self.env['stock.warehouse'].sudo().search([('name', '=ilike', warehouse_destiny + '%')],limit=1)
            location_from = self.env['stock.location'].sudo().search([('complete_name', '=ilike', location_origin + '%')],limit=1)
            location_to = self.env['stock.location'].sudo().search([('complete_name', '=ilike', location_destiny + '%')],limit=1)
            if not warehouse_from:
                orders_errors.append('Linea:' + str(pos) + ' - el almacén origen: ' + str(warehouse_origin) + ' no fue encontrado.')
            elif not warehouse_to:
                orders_errors.append('Linea:' + str(pos) + ' - el almacén destino: ' + str(warehouse_destiny) + ' no fue encontrado.')
            elif not location_from:
                orders_errors.append('Linea:' + str(pos) + ' - la ubicación origen : ' + str(location_origin) + ' no fue encontrada.')
            elif not location_to:
                orders_errors.append('Linea:' + str(pos) + ' - la ubicación destino : ' + str(location_destiny) + ' no fue encontrada.')
            elif not product:
                orders_errors.append('Linea:' + str(pos) + ' - el producto : ' + str(code_product) + ' no fue encontrado.')
            else:
                if len(groups) == 0:
                    groups.append({'from_warehouse_id': warehouse_from.id,
                                   'to_warehouse_id': warehouse_to.id,
                                   'from_location_id': location_from.id,
                                   'to_location_id': location_to.id,
                                   'internal_stock_transfer_line_ids': [(0,0,{'product_id': product.id, 'qty': quantity})]
                                   })
                else:
                    sw=0
                    for g in groups:
                        if g['from_warehouse_id'] == warehouse_from.id and g['to_warehouse_id'] == warehouse_to.id and \
                            g['from_location_id'] == location_from.id and g['to_location_id'] == location_to.id:
                            sw=1
                            break

                    if sw==1:
                        g['internal_stock_transfer_line_ids'].append((0,0,{'product_id': product.id, 'qty': quantity}))
                    else:
                        groups.append({'from_warehouse_id': warehouse_from.id,
                                       'to_warehouse_id': warehouse_to.id,
                                       'from_location_id': location_from.id,
                                       'to_location_id': location_to.id,
                                       'internal_stock_transfer_line_ids': [(0,0,{'product_id': product.id, 'qty': quantity})]
                                       })



        if len(groups)>0:
            internal_transfer.create(groups)

        self.logs = 'good'
        if orders_errors:
            message = ''
            for e in orders_errors:
                message += '*' + e + '\n'

            self.logs = message

        return {
            u'name': u'Resultado del proceso',
            u'type': u'ir.actions.act_window',
            u'view_mode': u'form',
            u'target': u'new',
            u'res_model': u'internal.transfer.import.wizard',
            u'res_id': self.id
        }

    def download_file_xlx(self):
        self.ensure_one()
        url = f'/l10n_cr_toy_extends/static/xlsx/CARGA_TRANSFERENCIA_INTERNA.xlsx'
        return {
            'name': _("Excel"),
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }



    def link_ywt_internal_stock_transfer_action(self):
        """ Return the action used to display orders when returning from customer portal. """
        # self.ensure_one()
        # return self.env.ref('sale.action_quotations_with_onboarding')
        action = self.env["ir.actions.actions"]._for_xml_id("ywt_internal_stock_transfer.ywt_internal_stock_transfer_action")
        return action





