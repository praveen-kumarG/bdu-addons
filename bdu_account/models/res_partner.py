# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Magnus
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, exceptions, models, _

class DeliveryTerms(models.Model):
    _name = 'delivery.terms'
    _description = 'Terms Of Delivery'
    _rec_name = 'name'

    name = fields.Char('Name')

class PartnerStatus(models.Model):
    _name = 'partner.status'
    _description = 'Status'
    _rec_name = 'name'

    name = fields.Char('Name')

class Partner(models.Model):
    _inherit = 'res.partner'

    #override base_partner_sequence method to change sequence number padding
    @api.multi
    def _get_next_ref(self, vals=None):
        return self.env['ir.sequence'].next_by_code('res.partner.seq')

    @api.multi
    def _needsRef(self, vals=None):
        """
        Override base_partner_sequence method
        Checks whether a sequence value should be assigned to a partner's 'ref'

        :param self: recordset(s) of the partner object
        :param vals: known field values of the partner object
        :return: true if a sequence value should be assigned to the\
                      partner's 'ref'
        """
        res = super(Partner, self)._needsRef(vals)
        # to check partner belongs to res users or res company, if yes no sequence created
        if self._context.get('no_partner_sequence', False):
            return False
        return res

    promille_id = fields.Char('Promille ID')
    pubble_id = fields.Char('Pubble ID')
    zeno_id = fields.Char('Zeno ID')
    exact_id = fields.Char('Exact ID')
    facebook = fields.Char('Facebook')
    twitter = fields.Char('Twitter')
    linkedIn = fields.Char('LinkedIn')
    instagram = fields.Char('Instagram')
    date_established = fields.Date('Date Established')
    delievery_terms = fields.Many2one('delivery.terms','Terms of delivery')
    status = fields.Many2one('partner.status','Status')
    newsletter_opt_out = fields.Boolean('Newsletter opt-out')

class Users(models.Model):
    _inherit = 'res.users'

    @api.model
    def create(self, vals):
        ctx = self._context.copy()
        ctx.update({'no_partner_sequence': True})
        self = self.with_context(ctx)
        return super(Users, self).create(vals)


class Company(models.Model):
    _inherit = "res.company"

    @api.model
    def create(self, vals):
        ctx = self._context.copy()
        ctx.update({'no_partner_sequence': True})
        self = self.with_context(ctx)
        return super(Company, self).create(vals)
