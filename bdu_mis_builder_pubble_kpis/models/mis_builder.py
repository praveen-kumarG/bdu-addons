# -*- coding: utf-8 -*-
import pdb
from odoo import api, fields, models

class MisReportInstancePeriod(models.Model):

    _inherit = 'mis.report.instance.period'

    operating_unit_ids = fields.Many2many('operating.unit',
                                          string='Operating Unit',
                                          required=False)

    @api.multi
    def _get_additional_query_filter(self, query):
        #let super do its job first
        aml_domain = super(MisReportInstancePeriod, self).\
            _get_additional_query_filter(query)
        #now additional filter under su account
        sudoself = self.sudo()
        if sudoself.report_instance_id.operating_unit_ids:
            aml_domain.append(
                ('operating_unit_id', 'in',
                 sudoself.report_instance_id.operating_unit_ids.ids))
        if sudoself.operating_unit_ids:
            aml_domain.append(
                ('operating_unit_id', 'in',
                 sudoself.operating_unit_ids.ids))
        return aml_domain
