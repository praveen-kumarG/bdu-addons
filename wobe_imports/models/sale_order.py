# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    job_id = fields.Many2one('wobe.job','Job Ref #',ondelete='set null', index=True)

    @api.multi
    def action_confirm(self):
        order_ids = []
        for order in self:
            if not self.job_id:
                order_ids.append(order.id)
                continue
            order.state = 'sale'
            order.confirmation_date = fields.Datetime.now()
            if self.env.context.get('send_email'):
                self.force_quotation_send()
            if self.env['ir.values'].get_default('sale.config.settings', 'auto_done_setting'):
                self.action_done()
            self.env.cr.commit()
        self._ids = order_ids
        return super(SaleOrder, self).action_confirm()

