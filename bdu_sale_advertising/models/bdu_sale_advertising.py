# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class SaleAdvertisingIssue(models.Model):
    _inherit = "sale.advertising.issue"

    crm_team_id = fields.Many2one('crm.team', 'Primary salesteam')

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    order_team_id = fields.Many2one(related='order_id.team_id', relation='crm.team',
                                    string='Salesteam', store=True)