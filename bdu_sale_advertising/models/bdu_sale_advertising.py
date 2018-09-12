# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class SaleAdvertisingIssue(models.Model):
    _inherit = "sale.advertising.issue"

    crm_team_id = fields.Many2one('crm.team', 'Primary salesteam')

