# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
import datetime


class AccountInvoice(models.Model):
    _inherit = ["account.invoice"]



    # TODO: check if this is needed?
    @api.multi
    def invoice_print(self):
        """ Print the invoice and mark it as sent
        """
        self.ensure_one()
        if self.type == 'out_refund':
            for line in self.invoice_line_ids:
                if not line.so_line_id:
                    line.so_line_id = line.origin_line_ids.sale_line_ids.id
        return super(AccountInvoice, self).invoice_print()

    def _get_refund_common_fields(self):
        res = super(AccountInvoice, self)._get_refund_common_fields()
        return res+['published_customer']

    @api.model
    def _refund_cleanup_lines(self, lines):
        if self.env.context.get('mode') == 'modify':
            result = super(AccountInvoice, self).with_context(mode=False)._refund_cleanup_lines(lines)
            for i in xrange(0, len(lines)):
                for name, field in lines[i]._fields.iteritems():
                    if name == 'so_line_id' and not lines[i][name]:
                        result[i][2][name] = lines[i]['sale_line_ids'].id
                        lines[i][name] = lines[i]['sale_line_ids'].id
                    if name == 'sale_line_ids':
                        result[i][2][name] = [(6, 0, lines[i][name].ids)]
                        lines[i][name] = False
        else:
            result = super(AccountInvoice, self)._refund_cleanup_lines(lines)
            for i in xrange(0, len(lines)):
                for name, field in lines[i]._fields.iteritems():
                    if name == 'so_line_id' and not lines[i][name]:
                        result[i][2][name] = lines[i]['sale_line_ids'].id
                        lines[i][name] = lines[i]['sale_line_ids'].id
        return result



class AccountInvoiceLine(models.Model):
    _inherit = ["account.invoice.line"]


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

