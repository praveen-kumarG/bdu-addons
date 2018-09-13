# -*- coding: utf-8 -*-
import pdb
from odoo import api, fields, models

class MisReportInstancePeriod(models.Model):

    _inherit = 'mis.report.instance.period'

    @api.multi
    def _get_additional_query_filter(self, query):
        
        #let super do its job first (although current implementation does not add anything)
        aml_domain = super(MisReportInstancePeriod, self).\
            _get_additional_query_filter(query)

        #add own analytic account filter
        analytic_account_id = self.env.context.get('analytic_account_id')
        if analytic_account_id:
            aml_domain.append(('analytic_account_id', '=', analytic_account_id))
        
        #additional filter made under su account for operating units
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
