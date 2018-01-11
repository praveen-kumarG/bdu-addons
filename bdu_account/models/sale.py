# -*- coding: utf-8 -*-

from odoo import api, fields, models, _



class Sale(models.Model):
    _inherit = ["sale.order"]


    @api.multi
    def print_quotation(self):

        if self.advertising == True:
            self.filtered(lambda s: s.state == 'approved2').write({'state': 'sent'})
            return self.env['report'].get_action(self, 'sale.report_saleorder')
        else:
            return super(Sale, self).print_quotation()