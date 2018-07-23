# -*- coding: utf-8 -*-

from odoo import api, fields, exceptions, models, _

class Partner(models.Model):
    _inherit = 'res.partner'
    
    
    @api.model
    def create(self, values):
        res = super(Partner, self).create(values)
        if res.user_ids:
            res.with_context({'falseCustomer':False}).write({'customer':False})
        return res

    @api.multi
    def write(self, values):
        res = super(Partner, self).write(values)
        if 'falseCustomer' in self.env.context:
            return res
        for partner in self:
            if partner.user_ids:
                partner.with_context({'falseCustomer':False}).write({'customer': False})
        return res
