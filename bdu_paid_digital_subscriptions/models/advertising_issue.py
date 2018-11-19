# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AdvertisingIssue(models.Model):
    _inherit = "sale.advertising.issue"

    digital_paywall = fields.Boolean('Digital paywall')
    #NOTE: the digital subscription boolean on the template indicates whether it is a digital only product

