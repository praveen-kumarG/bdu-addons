# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    job_id = fields.Many2one('wobe.job','Job Ref #',ondelete='set null', index=True, default=False)
    issue_date = fields.Date(related='job_id.issue_date')

    @api.multi
    def action_confirm(self):
        for order in self.filtered('job_id'):
            for orderline in order.order_line:
                if self.pricelist_id and self.partner_id:
                    orderline.price_unit = self.env['account.tax']._fix_tax_included_price_company(
                                                orderline._get_display_price(orderline.product_id),
                                                orderline.product_id.taxes_id, orderline.tax_id, self.company_id)
        return super(SaleOrder, self).action_confirm()
