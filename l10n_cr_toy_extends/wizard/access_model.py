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

class AccessModelWizard(models.TransientModel):
    _name = 'access.model.wizard'
    _description = 'Permisos de acceso para model'

    def _default_count(self):
        context = self.env.context
        if 'active_ids' in context:
            return len(self.env.context['active_ids'])
        else:
            return 1

    count = fields.Integer(default=_default_count)

    action = fields.Selection([('active','Activar'),('inactive','Inactivar')],string='Acción', required=True, default='inactive')
    access = fields.Selection([('read','Permiso para leer'),
                               ('write','Permiso para escritura'),
                               ('create','Acceso para crear'),
                               ('delete','Permiso para eliminar')], string='Permisos', required=True, default='write')

    # access_read = fields.Boolean('Permiso para leer')
    # access_write = fields.Boolean('Permiso para escritura')
    # access_create = fields.Boolean('Acceso para crear')
    # access_delete = fields.Boolean('Permiso para eliminar')

    def process(self, context=None):
        context = context or self.env.context
        model_ids = ('active_ids' in context and context['active_ids']) or []
        model = context['active_model']

        model_active_ids = self.env[model].sudo().browse(model_ids)
        action = False
        if self.action == 'active':
            action = True
        else:
            action = False

        if model_active_ids:
            for m in model_active_ids:
                if m.access_ids:
                    for access in m.access_ids:
                        if self.access == 'read':
                            access.perm_read = action
                        elif self.access == 'write':
                            access.perm_write = action
                        elif self.access == 'create':
                            access.perm_write = action
                        elif self.access == 'delete':
                            access.perm_unlink = action



