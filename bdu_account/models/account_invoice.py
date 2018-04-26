# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
import datetime


class AccountInvoice(models.Model):
    _inherit = ["account.invoice"]

#    published_customer = fields.Many2one('res.partner', 'Advertiser', domain=[('customer','=',True)])


    # TODO: check if this is needed?
    @api.multi
    def invoice_print(self):
        """ Print the invoice and mark it as sent
        """
        self.ensure_one()
        self.sent = True
        return self.env['report'].get_action(self, 'account.report_invoice')

    def _get_refund_common_fields(self):
        res = super(AccountInvoice, self)._get_refund_common_fields()
        return res+['published_customer']

class AccountInvoiceLine(models.Model):
    _inherit = ["account.invoice.line"]

    refund_orig_line_id = fields.Many2one('account.invoice.line', 'Relation from Refund Line to original Invoice Line')

    @api.model
    def create(self, vals):
        ctx = self.env.context.copy()
        line_obj = super(AccountInvoiceLine, self).create(vals)
        if 'active_model' in ctx:
            if ctx.get('active_model') in ('sale.order','sale.order.line'):
                for sale_line_obj in line_obj.sale_line_ids:
                    description = False
                    if sale_line_obj.company_id.use_bduprint and line_obj.product_id == sale_line_obj.product_id and sale_line_obj.product_id.product_tmpl_id.invoice_description:
                        description = sale_line_obj.name
                    if description:
                        line_obj.write({'name':description})
        return line_obj

    @api.model
    def _refund_cleanup_lines(self, lines):
        """ Convert records to dict of values suitable for one2many line creation

            :param recordset lines: records to convert
            :return: list of command tuple for one2many line creation [(0, 0, dict of valueis), ...]
        """
        result = super(AccountInvoiceLine, self)._refund_cleanup_lines(lines)
        for i in xrange(0, len(lines)):
            result[i][2]['refund_orig_line_id'] = lines[i].id
        return result

    @api.multi
    def _get_advertising_details_for_credit(self):
        self.ensure_one()
        if self.refund_orig_line_id:
            line_obj = self.search([('id','=',self.refund_orig_line_id.id)])
            return line_obj.sale_line_ids


#    so_number = fields.Char(string='Order Number')
#    sol_issuedt = fields.Date(string='Issue Date')
#    sol_title = fields.Char(string='Title')
#    sol_discount = fields.Float(string='Discount', digits=dp.get_precision('Account'))
#    sol_computed_discount = fields.Float(string='Computed Discount', digits=dp.get_precision('Account'))
