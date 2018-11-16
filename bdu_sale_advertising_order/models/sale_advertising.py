# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = ["sale.order"]

    magazine = fields.Boolean(string='Vakmedia Achtergrond Offerte', default=False)

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.depends('medium')
    @api.multi
    def _compute_magazine(self):
        """
        Compute if order_line.magazine is True.
        """
        for line in self.filtered('advertising'):
            if line.medium and line.medium in [self.env.ref('sale_advertising_order.magazine_advertising_category'),self.env.ref('sale_advertising_order.magazine_online_advertising_category')]:
                line.magazine = True

    magazine = fields.Boolean(compute='_compute_magazine', string='Magazine', store=True)