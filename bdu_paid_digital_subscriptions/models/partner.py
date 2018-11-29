# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    #For subscriptions coming from Bakker Baarn
    afas_id = fields.Char('Afas ID')


