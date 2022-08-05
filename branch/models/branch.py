# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)
import pytz
from datetime import datetime, date, timedelta

class ResBranch(models.Model):
    _name = 'res.branch'
    _description = 'Branch'

    name = fields.Char(required=True)
    company_id = fields.Many2one('res.company', required=True)
    telephone = fields.Char(string='Telephone No')
    address = fields.Text('Address')

    @api.model
    def _cron_account_move_close_branch(self):
        _logger.info("Ejecutando CRON de asiento contable para caja - BRANCH")
        event_cron_id = self.env.ref('branch.ir_cron_move_close_branch')
        if event_cron_id.active:
            self.sudo()._account_move_close_branch(False, False, False, False, event_cron_id, True)

        else:
            print('Cron de cierre de caja no activo')



    @api.model
    def _account_move_close_branch(self,branch_ids,term_paid_ids,date_from,date_to, event_cron_id,cron):

        journal_id = self.env.ref('branch.close_branch_journal')
        user_type_id = self.env.ref('account.data_account_type_liquidity').id

        if cron:
            time_sytem = event_cron_id.nextcall
            date_costa_rica = (time_sytem.astimezone(pytz.timezone("America/Costa_Rica")) - timedelta(hours=5)).date()
        else:
            date_costa_rica = datetime.now(pytz.timezone("America/Costa_Rica")).date()

        aml = self.env['account.move.line'].sudo()

        domain_branch = [('parent_state', '=', 'posted'),
                         ('account_id.user_type_id', '=', user_type_id),
                         ('journal_id', '!=', journal_id.id),
                         ('move_comission_id', '=', False)]
        if not date_to and not date_from:
           domain_branch.append(('date', '=', date_costa_rica))
        else:
            domain_branch.append(('date', '<=', date_from))
            domain_branch.append(('date', '>=', date_to))


        if branch_ids:
            domain_branch.append(('branch_id','in',branch_ids.ids))

        groups_branch = aml.read_group(domain_branch,
                                       fields=['branch_id'], groupby=['branch_id'],
                                       )

        for group in groups_branch:
            _logger.info(group['branch_id'][1])
            domain_forma_pago = [('parent_state', '=', 'posted'),
                                 ('branch_id', '=', group['branch_id'][0]),
                                 ('account_id.user_type_id', '=', user_type_id),
                                 ('journal_id', '!=', journal_id.id),
                                 ('move_comission_id', '=', False)]
            if not date_to and not date_from:
                domain_forma_pago.append(('date', '=', date_costa_rica))

            else:
                domain_forma_pago.append(('date', '<=', date_from))
                domain_forma_pago.append(('date', '>=', date_to))

            if term_paid_ids:
                domain_forma_pago.append(('forma_pago_id','in',term_paid_ids.ids))

            groups_forma_pago = aml.read_group(domain_forma_pago,
                                               fields=['forma_pago_id'], groupby=['forma_pago_id'])

            if groups_forma_pago:
                for fp in groups_forma_pago:
                    if fp['forma_pago_id']==False:
                        paid_term_id = False
                    else:
                        paid_term_id = fp['forma_pago_id'][0]


                    domain_lines = [('parent_state', '=', 'posted'),
                                    ('branch_id', '=', group['branch_id'][0]),
                                    ('forma_pago_id','=', paid_term_id),
                                    ('journal_id','!=',journal_id.id),
                                    ('move_comission_id','=',False)]

                    if not date_to and not date_from:
                        domain_lines.append(('date', '=', date_costa_rica))
                    else:
                        domain_lines.append(('date', '<=', date_from))
                        domain_lines.append(('date', '>=', date_to))


                    lines = aml.search(domain_lines)
                    if lines:
                        self._create_moves_close_cash(lines,journal_id, group['branch_id'], fp['forma_pago_id'],date_costa_rica)

            else:
                _logger.info("No se encontró movimientos en líenas para este grupo %s" % group['branch_id'][1])


    def _create_moves_close_cash(self,lines,journal_id, branch_id, fp_id, date_costa_rica):
        array_lines = []
        move_lines = []

        if lines:
            _logger.info('N° movimientos %s' % (len(lines)))
            info = []
            amount_credit = 0.0
            comission_bank = 0.0
            retention_isr = 0.0
            retention_iva = 0.0
            sum_destinty = 0.0
            for l in lines:
                if l.account_id.active_comission and not l.move_comission_id:
                    print(
                        'La cuenta si tiene activa el check para comision bancaria y no tiene movimiento de comision ')
                    print(l.account_id.code)
                    if l.debit > 0.0:
                        amount_credit += l.debit
                        if not info:
                            info.append({'line':l, 'name': l.account_id.name, 'debit': 0.0, 'credit': l.debit,'account': l.account_id})
                        else:
                            x = filter(lambda i: i['account'].id == l.account_id.id, info)
                            y = list(x)[0]
                            if y:
                                y['credit']+=l.debit
                            else:
                                info.append({'line': l, 'name': l.account_id.name, 'debit': 0.0, 'credit': l.debit,
                                             'account': l.account_id})

                        if l.account_id.comission_bank > 0.0:
                            comission_bank += round(l.debit * (l.account_id.comission_bank / 100), 2)
                        if l.account_id.retention_isr > 0.0:
                            retention_isr += round(l.debit * (l.account_id.retention_isr / 100), 2)
                        if l.account_id.retention_iva > 0.0:
                            retention_iva += round(l.debit * (l.account_id.retention_iva / 100), 2)
                        # if l.account_id.account_bank_id:
                        #     account_credit = l.account_id.account_bank_id
                            # sum_destinty += amount_credit - (comission_bank +retention_isr+retention_iva)

                else:
                    _logger.info(
                        'La cuenta %s no tiene activa el check para comision bancaria' % (l.account_id.code))

            if info:

                if comission_bank > 0.0:
                    info.append({'line': info[0]['line'],'name': 'Comisión bancaria', 'debit': comission_bank, 'credit': 0.0,
                                 'account': info[0]['account'].comission_bank_account})

                if retention_isr > 0.0:
                    info.append({'line': info[0]['line'],'name': 'Retención ISR', 'debit': retention_isr, 'credit': 0.0,
                                 'account': info[0]['account'].retention_isr_account})

                if retention_iva > 0.0:
                    info.append({'line': info[0]['line'],'name': 'Retención IVA', 'debit': retention_iva, 'credit': 0.0,
                                 'account': info[0]['account'].retention_iva_account})

                sum_destinty = amount_credit - (comission_bank + retention_isr + retention_iva)
                # Asiento destino
                if sum_destinty > 0.0:
                    info.append({'line': info[0]['line'],'name': 'Destino bancario', 'debit': sum_destinty, 'credit': 0.0,'account': info[0]['account'].account_bank_id})

                for i in info:
                    json_lines = {
                        'name': i['name'],
                        'account_id': i['account'].id,
                        'currency_id': i['line'].currency_id.id,
                        'debit': i['debit'],
                        'credit': i['credit'],
                        'amount_currency': 0.0,
                    }
                    array_lines.append((0, 0, json_lines))

                move_lines.append(info[0]['line'])

            print('----DEBITO----')
            print('Comission bank : ' + str(comission_bank))
            print('Retencicon ISR : ' + str(retention_isr))
            print('Retencion IVA : ' + str(retention_iva))
            print('Desitno : ' + str(sum_destinty))
            print('----CREDITO----')
            print('credito : ' + str(amount_credit))


        if len(array_lines) > 0:
            _logger.info("Creando asiento contable para branch %s " % (branch_id[1]))
            forma_pago = 'SIN FORMA PAGO' if fp_id==False else fp_id[1]
            _logger.info("Creando asiento contable para Forma de pago %s " % (forma_pago))
            move_to_create = {
                'name': '/',
                'move_type': 'entry',
                'journal_id': journal_id.id,
                'date': date_costa_rica,
                'partner_id': self.env.company.partner_id.id,
                'line_ids': array_lines,
                'branch_id': branch_id[0],
                'forma_pago_id': False if fp_id==False else fp_id[0],
            }

            if move_to_create:
                move = self.env['account.move'].sudo().create(move_to_create)
                for x in move_lines:
                    x.move_comission_id = move
                _logger.info('Asiento contable creado por cierre de caja:')
                _logger.info(move)
        else:
            _logger.info('No hay líneas por crear')