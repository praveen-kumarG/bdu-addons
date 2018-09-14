# -*- coding: utf-8 -*-
from odoo import api, fields, models
import pdb
class MisReportInstancePeriod(models.Model):

    _inherit = 'mis.report.instance.period'

    @api.multi
    def _get_additional_query_filter(self, query):
        pdb.set_trace()
        #let super do its job first (although current implementation does not add anything)
        aml_domain = super(MisReportInstancePeriod, self).\
            _get_additional_query_filter(query)

        #get model we work on and full view on data
        model_id = query.model_id.id
        sudoself = self.sudo()

        #only add analytic filter if there is corresponding field in model to query
        fields   = sudoself.env['ir.model.fields'].search([('model_id','=',model_id),('name','=',u'analytic_account_id')])
        if len(fields)==1 :
            #and if used/set
            analytic_account_id = self.env.context.get('analytic_account_id')
            if analytic_account_id:
                aml_domain.append(('analytic_account_id', '=', analytic_account_id))
            
        #only add operating unit filter if model to query has such a field
        fields   = sudoself.env['ir.model.fields'].search([('model_id','=',model_id),('name','=',u'operating_unit_id')])
        if len(fields)==1 :
            #and if operating unit is used/set in query
            if sudoself.report_instance_id.operating_unit_ids:
                aml_domain.append(
                    ('operating_unit_id', 'in',
                     sudoself.report_instance_id.operating_unit_ids.ids))
            if sudoself.operating_unit_ids:
                aml_domain.append(
                    ('operating_unit_id', 'in',
                     sudoself.operating_unit_ids.ids))
        
        return aml_domain
