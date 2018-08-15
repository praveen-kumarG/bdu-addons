# -*- coding: utf-8 -*-
from odoo import http

# class MisKpiCollector(http.Controller):
#     @http.route('/mis_kpi_collector/mis_kpi_collector/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mis_kpi_collector/mis_kpi_collector/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mis_kpi_collector.listing', {
#             'root': '/mis_kpi_collector/mis_kpi_collector',
#             'objects': http.request.env['mis_kpi_collector.mis_kpi_collector'].search([]),
#         })

#     @http.route('/mis_kpi_collector/mis_kpi_collector/objects/<model("mis_kpi_collector.mis_kpi_collector"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mis_kpi_collector.object', {
#             'object': obj
#         })