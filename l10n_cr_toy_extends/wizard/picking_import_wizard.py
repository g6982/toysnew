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
from odoo.tests import Form

ACTION = [('automatic','Automática'),('manual','Manualmente')]
ACTION_PARTIAL = [('yes','Realizar la entrega parcial(Creará otro picking con las entregas faltantes)'),
                  ('no','No hacer entrega parcial(Cierra el picking y queda en estado "realizado")'),
                  ('cancel','Cancelar la entrega parcial(El usuario verificará el picking, solo actualiza las cantidad realizadas)')]
class PickingImportWizard(models.TransientModel):
    _name = 'picking.import.wizard'
    _description = 'Importacion para actualización de entregas en picking'

    file = fields.Binary(string="Subir archivo (.xlsx)", required=False)
    file_name = fields.Char(string="Nombre del archivo")
    company_id = fields.Many2one('res.company', string=u'Compañia', default=lambda self: self.env.user.company_id)
    logs = fields.Text('Advertencias')
    action = fields.Selection(ACTION, default='manual',string='Desea realizar la transferencia : ')
    action_partial = fields.Selection(ACTION_PARTIAL, default='cancel',string='Para el caso de entregas parciales ')


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
        picking_to_confirm = []
        pos = 1
        for i in range(desde, hasta):
            pos+=1
            code_picking = sheet.cell(i,0).value
            code_location = sheet.cell(i,1).value
            code_product= sheet.cell(i,2).value
            quantity = sheet.cell(i,3).value

            stock_picking = self.env['stock.picking'].sudo().search([('name','=',code_picking.strip())])
            location = self.env['stock.location'].sudo().search([('complete_name', '=', code_location.strip())])
            product = self.env['product.product'].sudo().search([('default_code', '=', code_product.strip())])

            if not stock_picking:
                orders_errors.append('Linea:' + str(pos) + ' - el picking : ' + str(code_picking) + ' no fue encontrado.')
            elif not location:
                orders_errors.append('Linea:' + str(pos) + ' - la ubicación : ' + str(code_location) + ' no fue encontrado.')
            elif not product:
                orders_errors.append('Linea:' + str(pos) + ' - el producto : ' + str(code_product) + ' no fue encontrado.')
            elif stock_picking and location and product:
                if stock_picking.state not in ('assigned'):
                    orders_errors.append('Linea:' + str(pos) + ' - el picking : ' + str(code_picking) + ' esta en estado : ' + str(stock_picking.state))
                else:
                    loc = stock_picking.move_line_ids_without_package.filtered(lambda l: l.location_id.id == location.id)
                    pro = stock_picking.move_line_ids_without_package.filtered(lambda p: p.product_id.id == product.id)
                    qty = stock_picking.move_line_ids_without_package.filtered(lambda q: q.product_uom_qty < quantity and q.product_id.id == product.id and q.location_id.id == location.id)
                    if not loc.exists():
                        orders_errors.append('Linea:' + str(pos) + ' - la ubicación: ' + str(code_location) + ' no fue encontrado en este picking.')
                    elif not pro.exists():
                        orders_errors.append('Linea:' + str(pos) + ' - la ubicación: ' + str(code_product) + ' no fue encontrado en este picking.')
                    elif qty.exists():
                        orders_errors.append('Linea:' + str(pos) + ' - la cantidad a realizar : ' + str(quantity) + ' excede a la cantidad reservada en este picking')
                    else:
                        stock_picking.move_line_ids_without_package.filtered(lambda x: x.location_id.id == location.id and x.product_id.id == product.id).write({'qty_done': quantity})

                        if not stock_picking in picking_to_confirm:
                            picking_to_confirm.append(stock_picking)


            else:
                orders_errors.append('Linea:' + str(pos) + ' - ERROR NO CONOCIDO')

        self.logs = 'good'
        if orders_errors:
            message = ''
            for e in orders_errors:
                message += '*' + e + '\n'

            self.logs = message

        #TODO: NO VALIDAR LOS PICKINGS
        if self.action =='automatic':
            for pick in picking_to_confirm:
                res = pick.button_validate()
                if type(res)==bool:
                    pass
                elif 'res_model' in res:
                    if self.action_partial == 'no':
                        Form(self.env[res['res_model']].with_context(res['context'])).save().process_cancel_backorder()
                    elif self.action_partial == 'yes':
                        Form(self.env[res['res_model']].with_context(res['context'])).save().process()
                    else:
                        Form(self.env[res['res_model']].with_context(res['context'])).save().cancel()
                else:
                    pass


        return {
            u'name': u'Resultado del proceso de picking',
            u'type': u'ir.actions.act_window',
            u'view_mode': u'form',
            u'target': u'new',
            u'res_model': u'picking.import.wizard',
            u'res_id': self.id
        }



    def download_file_xlx(self):
        self.ensure_one()
        url = f'/l10n_cr_toy_extends/static/xlsx/CARGA_MOVIMIENTOS_EN_PICKING.xlsx'
        return {
            'name': _("Excel"),
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }



    def link_quotations_action(self):
        action = self.env["ir.actions.actions"]._for_xml_id("stock.stock_move_line_action")
        return action

