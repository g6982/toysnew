# -*- coding: utf-8 -*-
# from odoo import http


# class L10nCrToyExtends(http.Controller):
#     @http.route('/l10n_cr_toy_extends/l10n_cr_toy_extends/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/l10n_cr_toy_extends/l10n_cr_toy_extends/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('l10n_cr_toy_extends.listing', {
#             'root': '/l10n_cr_toy_extends/l10n_cr_toy_extends',
#             'objects': http.request.env['l10n_cr_toy_extends.l10n_cr_toy_extends'].search([]),
#         })

#     @http.route('/l10n_cr_toy_extends/l10n_cr_toy_extends/objects/<model("l10n_cr_toy_extends.l10n_cr_toy_extends"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('l10n_cr_toy_extends.object', {
#             'object': obj
#         })
