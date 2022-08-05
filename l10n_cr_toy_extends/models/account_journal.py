# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round
from odoo.tools.float_utils import float_repr


class AccountJournal(models.Model):
    _inherit = "account.journal"

    account_expense_id = fields.Many2one('account.account',string='Cuenta para gasto')