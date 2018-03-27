# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.queue_job.job import job, related_action
from odoo.addons.queue_job.exception import FailedJobError


class AccountInvoiceConfirm(models.TransientModel):
    """
    This wizard will confirm the all the selected draft invoices if required via job queue
    """
    _inherit = "account.invoice.confirm"

    chunk_size = fields.Integer('Chunk Size Job Queue', default=50)
    job_queue = fields.Boolean('Process via Job Queue', default=False)
    execution_datetime = fields.Datetime('Job Execution not before', default=fields.Datetime.now())

    @api.multi
    def invoice_confirm(self):
        if not self.job_queue:
            return super(AccountInvoiceConfirm, self).invoice_confirm()
#        eta = fields.Datetime.from_string(self.execution_datetime)
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        self.with_delay()._split_jobs(active_ids)

        return True

    @job
    def _split_jobs(self, inv_ids):
        size = self.chunk_size
        eta = fields.Datetime.from_string(self.execution_datetime)
        for x in xrange(0, len(inv_ids), size):
            chunk = inv_ids[x:x + size]
            self.with_delay(eta=eta).invoice_confirm_jobqueue(chunk)

    @job
    @api.multi
    def invoice_confirm_jobqueue(self, chunk):
        for record in self.env['account.invoice'].browse(chunk):
            if record.state not in ('draft', 'proforma', 'proforma2'):
                raise FailedJobError(_("Selected invoice(s) cannot be confirmed "
                                       "as they are not in 'Draft' or 'Pro-Forma' state. "
                                       "Reference/Description: '%s'  "
                                       "Number: '%s'") % (record.name, record.number))
            record.action_invoice_open()

