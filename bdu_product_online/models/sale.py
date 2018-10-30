# -*- coding: utf-8 -*-
import pdb
from odoo import api, fields, models


class ProductAnnouncementOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    attachment_ids = fields.Many2many('ir.attachment', string="Attachment(s)")
    landing_page   = fields.Char('Landing page')
    retarget       = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Retarget')
    profile        = fields.Many2many('online.profile', string="Profile")


