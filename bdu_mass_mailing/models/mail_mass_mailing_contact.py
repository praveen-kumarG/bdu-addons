# -*- coding: utf-8 -*-
# Copyright 2015 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2015 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# Copyright 2015 Javier Iniesta <javieria@antiun.com>
# Copyright 2017 David Vidal <david.vidal@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models


class MailMassMailingContact(models.Model):
    _inherit = 'mail.mass_mailing.contact'

    partner_id = fields.Many2one(comodel_name='res.partner', string="Partner",
                                 domain=[('email', '!=', False)])
    user_id = fields.Many2one(related='partner_id.user_id', string="Client Owner", store=True)
    category_id = fields.Many2many(related='partner_id.category_id', string="Customer Labels", store=True)
    contact_id = fields.Many2one(compute='_compute_contact', comodel_name='res.partner',string="Contact Person", store=True)
    sector_id = fields.Many2one(related='partner_id.sector_id', string="Main Sector", store=True)

    @api.depends('partner_id')
    def _compute_contact(self):
        for contact in self:
            if contact.partner_id.child_ids:
                c = self.env['res.partner'].search([('id','in', contact.partner_id.commercial_partner_id.child_ids),('type','=','contact')])
                contact.contact_id = c[0].id

