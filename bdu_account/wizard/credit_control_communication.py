# -*- coding: utf-8 -*-
from odoo import api, fields, models

class CreditCommunication(models.TransientModel):

    _inherit = "credit.control.communication"

    @api.model
    def _generate_comm_from_credit_lines(self, lines):
        """ Aggregate credit control line by partner, level, and currency
        It also generate a communication object per aggregation.
        """
        comms = self.browse()
        if not lines:
            return comms
        sql = (
            "SELECT distinct partner_id, policy_level_id, "
            " credit_control_line.currency_id, "
            " credit_control_line.company_id, " #get company_id from line
            " credit_control_policy_level.level"
            " FROM credit_control_line JOIN credit_control_policy_level "
            "   ON (credit_control_line.policy_level_id = "
            "       credit_control_policy_level.id)"
            " WHERE credit_control_line.id in %s"
            " ORDER by credit_control_policy_level.level, "
            "          credit_control_line.currency_id"
        )
        cr = self.env.cr
        cr.execute(sql, (tuple(lines.ids),))
        res = cr.dictfetchall()
        company_currency = self.env.user.company_id.currency_id
        for group in res:
            data = {}
            level_lines = self._get_credit_lines(lines.ids,
                                                 group['partner_id'],
                                                 group['policy_level_id'],
                                                 group['currency_id'],
                                                 )
            data['credit_control_line_ids'] = [(6, 0, level_lines.ids)]
            data['partner_id'] = group['partner_id']
            data['current_policy_level'] = group['policy_level_id']
            data['currency_id'] = group['currency_id'] or company_currency.id
            data['company_id'] = group['company_id'] or self.env.user.company_id.id #added company_id
            comm = self.create(data)
            comms += comm
        return comms