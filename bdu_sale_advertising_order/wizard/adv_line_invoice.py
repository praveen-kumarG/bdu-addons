# -*- coding: utf-8 -*-
# Copyright 2018 Magnus ((www.magnus.nl).)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AdOrderLineMakeInvoice(models.TransientModel):
    _inherit = "ad.order.line.make.invoice"
    _description = "Advertising Order Line Make_invoice"

    @api.multi
    def make_invoices_from_lines(self):
        """
             To make invoices.
        """
        context = self._context
        if context.get('active_ids', []):
            lids = context.get('active_ids', [])
            OrderLines = self.env['sale.order.line'].browse(lids)
            magazines = OrderLines.filtered('magazine')
            non_magazines = OrderLines - magazines
            if not (len(magazines) == 0 or len(non_magazines) == 0):
                raise UserError(_('You can only invoice either Magazine order lines '
                                  'or Non-Magazine order lines, but not both'))
        return super(AdOrderLineMakeInvoice, self).make_invoices_from_lines()