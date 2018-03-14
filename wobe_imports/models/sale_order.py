# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    job_id = fields.Many2one('wobe.job','Job Ref #', ondelete='set null', index=True, default=False)
    issue_date = fields.Date(related='job_id.issue_date', store=True)

    @api.multi
    def action_confirm(self):
        for order in self.filtered('job_id'):
            for orderline in order.order_line:
                if self.pricelist_id and self.partner_id:
                    orderline.price_unit = self.env['account.tax']._fix_tax_included_price_company(
                                                orderline._get_display_price(orderline.product_id),
                                                orderline.product_id.taxes_id, orderline.tax_id, self.company_id)
        return super(SaleOrder, self).action_confirm()

    @api.model
    def create(self, vals):
        """Fill the payment_term_id & user_id from the partner if none is provided on
        creation, using same method as upstream."""
        onchanges = {
            'onchange_partner_id': ['payment_term_id'],
            'onchange_partner_id': ['user_id'],
        }
        for onchange_method, changed_fields in onchanges.items():
            if any(f not in vals for f in changed_fields):
                order = self.new(vals)
                getattr(order, onchange_method)()
                for field in changed_fields:
                    if field not in vals and order[field]:
                        vals[field] = order._fields[field].convert_to_write(
                            order[field], order,
                        )
        if not vals.get('user_id',False):
            vals['user_id'] = self.env.user.id
        return super(SaleOrder, self).create(vals)
