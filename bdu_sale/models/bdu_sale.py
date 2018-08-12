# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class SaleAdvertisingIssue(models.Model):
    _inherit = "sale.advertising.issue"
    group_id = fields.Many2one('crm.team', 'Filter group')

