# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from itertools import groupby


class Sale(models.Model):
    _inherit = ["sale.order"]

    @api.multi
    def print_quotation(self):

        if self.advertising == True:
            self.filtered(lambda s: s.state == 'approved2').write({'state': 'sent'})
            return self.env['report'].get_action(self, 'sale.report_saleorder')
        else:
            return super(Sale, self).print_quotation()

    #overridden order_lines_layouted to sort lines By issue_date
    @api.multi
    def order_lines_layouted(self):
        """
        Returns this order lines classified by sale_layout_category and separated in
        pages according to the category pagebreaks. Used to render the report.
        """
        self.ensure_one()
        report_pages = [[]]
        for category, lines in groupby(self.order_line.sorted(key=lambda b: b.issue_date), lambda l: l.layout_category_id):
            # If last added category induced a pagebreak, this one will be on a new page
            if report_pages[-1] and report_pages[-1][-1]['pagebreak']:
                report_pages.append([])
            # Append category to current report page
            report_pages[-1].append({
                'name': category and category.name or 'Uncategorized',
                'subtotal': category and category.subtotal,
                'pagebreak': category and category.pagebreak,
                'lines': list(lines)
            })

        return report_pages