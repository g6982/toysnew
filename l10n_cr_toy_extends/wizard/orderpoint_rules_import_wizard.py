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

class OrderpointRulesImportWizard(models.TransientModel):
    _name = 'orderpoint.rules.import.wizard'
    _description = 'Importación Reglas de abastecimiento'

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

        sw_orderpoint = self.env['stock.warehouse.orderpoint'].sudo()

        pos = 1
        for i in range(desde, hasta):
            pos += 1
            code_product = sheet.cell(i,0).value
            name_warehouse = sheet.cell(i,1).value
            name_location = sheet.cell(i,2).value
            quantity_min = sheet.cell(i,3).value
            quantity_max = sheet.cell(i,4).value
            quantity_mul = sheet.cell(i,5).value


            product = self.env['product.product'].sudo().search([('default_code', '=', code_product)])
            warehouse = self.env['stock.warehouse'].sudo().search([('name', '=ilike', name_warehouse + '%')])
            location = self.env['stock.location'].sudo().search([('complete_name', '=ilike', name_location + '%')])
            if not warehouse:
                orders_errors.append('Linea:' + str(pos) + ' - el almacén : ' + str(name_warehouse) + ' no fue encontrado.')
            elif not location:
                orders_errors.append('Linea:' + str(pos) + ' - la ubicación : ' + str(name_location) + ' no fue encontrada.')
            elif not product:
                orders_errors.append('Linea:' + str(pos) + ' - el producto : ' + str(code_product) + ' no fue encontrado.')
            elif location and product:
                sw_orderpoint_find = sw_orderpoint.search([('warehouse_id','=',warehouse.id),
                                                           ('location_id','=',location.id),
                                                           ('product_id','=',product.id),
                                                           ('company_id','=', self.company_id.id),
                                                           ], limit=1)
                if sw_orderpoint_find:
                    sw_orderpoint_find.write({
                        'warehouse_id': warehouse.id,
                        'location_id': location.id,
                        'product_id': product.id,
                        'product_min_qty': quantity_min,
                        'product_max_qty': quantity_max,
                        'qty_multiple': quantity_mul,
                    })
                else:
                    sw_orderpoint.create({
                        'warehouse_id': warehouse.id,
                        'location_id': location.id,
                        'product_id': product.id,
                        'product_min_qty': quantity_min,
                        'product_max_qty': quantity_max,
                        'qty_multiple': quantity_mul,
                    })

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
            u'res_model': u'orderpoint.rules.import.wizard',
            u'res_id': self.id
        }

    def download_file_xlx(self):
        self.ensure_one()
        url = f'/l10n_cr_toy_extends/static/xlsx/CARGA_REGLAS_ABASTECIMIENTO.xlsx'
        return {
            'name': _("Excel"),
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }



    def link_action_orderpoint(self):
        """ Return the action used to display orders when returning from customer portal. """
        # self.ensure_one()
        # return self.env.ref('sale.action_quotations_with_onboarding')
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_orderpoint")
        return action





