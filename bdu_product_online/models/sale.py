# -*- coding: utf-8 -*-
import pdb
from odoo import api, fields, models


class ProductAnnouncementOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    online_attachment_ids     = fields.Many2many('ir.attachment', string="Attachment(s)")
    online_url_to_material    = fields.Char('URL material')

    online_landing_page       = fields.Char('Landing page')
    online_retarget           = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Retarget')
    online_profile            = fields.Many2many('online.profile', string="Profile")
    online_from_date          = fields.Date('Show from')
    online_to_date            = fields.Date('Show until')
    online_adv_issue_ids      = fields.Many2many('sale.advertising.issue', string='Publiced in')
    online_notes              = fields.Text('Notes') 


