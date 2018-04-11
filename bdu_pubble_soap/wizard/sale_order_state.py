# -*- coding: utf-8 -*-
from odoo import models, api, _
from odoo.exceptions import UserError
from odoo.addons.queue_job.job import job, related_action
from odoo.addons.queue_job.exception import FailedJobError

class SaleOrderPubble(models.TransientModel):
    """
    This wizard will update all the selected orders in Pubble
    """

    _name = "sale.order.pubble"
    _description = "Update the selected sale orders in Pubble"

    @api.multi
    def sale_order_update_pubble(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        orders = self.env['sale.order'].browse(active_ids)
        for order in orders:
            if order.state not in ('sale') or not order.advertising:
                raise UserError(
                        _("Selected order(s) cannot be updated to Pubble as they are not in 'Sale', or 'Done' state"
                          " or they are not Advertising Orders."))
        orders.with_delay().action_pubble('update', False)
        return {'type': 'ir.actions.act_window_close'}




