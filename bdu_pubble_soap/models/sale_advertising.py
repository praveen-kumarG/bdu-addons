# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2017 Magnus (<http://www.magnus.nl>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
from suds.client import Client
from odoo.addons.queue_job.job import job, related_action
from odoo.addons.queue_job.exception import FailedJobError
import datetime


class SaleOrder(models.Model):
    _inherit = ["sale.order"]

    @api.depends('order_line.line_pubble_allow')
    @api.multi
    def _pubble_allow(self):
        for order in self:
            order.order_pubble_allow = False
            for line in order.order_line:
                if line.line_pubble_allow:
                    order.order_pubble_allow = True
                    break

    @api.depends('order_line.pubble_sent')
    @api.multi
    def _pubble_sent(self):
        for order in self:
            order.pubble_sent = False
            for line in order.order_line:
                if line.pubble_sent:
                    order.pubble_sent = True
                    break


    order_pubble_allow = fields.Boolean(compute=_pubble_allow, string='Allow to Pubble', default=False, store=True)
    date_sent_pubble = fields.Date('Date Sent to Pubble', index=True,
                                    help="Date on which sales order is sent to Pubble.")
    pubble_sent = fields.Boolean(compute=_pubble_sent, string='Order to Pubble', default=False, store=True)
    publog_id = fields.Many2one('sofrom.odooto.pubble')



    def action_pubble(self, arg):
        self.ensure_one()
        res = self.transfer_order_to_pubble(arg)
#        self._cr.commit()
        if self.order_pubble_allow:
            self.send_to_pubble(res)
        return True


    def send_to_pubble(self, res):
        res.with_delay().call_wsdl()
        self.write({'publog_id': res.id})
        for line in res.pubble_so_line:
            self.env['sale.order.line'].search([('id', '=', line.ad_extplacementid)]).write({'pubble_sent': True})

    @api.multi
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self.filtered("advertising"):
            order.action_pubble('update')
        return res



    @api.multi
    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        if ('partner_id' or 'published_customer' or 'advertising_agency' ) in vals:
            for order in self.filtered(lambda s: s.order_pubble_allow and s.advertising):
                order.action_pubble('update')
        return res


    @api.multi
    def action_cancel(self):
        for order in self.filtered(lambda s: s.state == 'sale' and s.advertising):
            order.pubble_delete()
        return super(SaleOrder, self).action_cancel()

    @api.multi
    def pubble_delete(self):
        self.ensure_one()
        self.action_pubble('delete')

    @api.multi
    def transfer_order_to_pubble(self, arg):
        self.ensure_one()
        del_param = True
        if arg == 'delete':
            del_param = False
        if not self.order_pubble_allow:
            vals = {
                'sale_order_id': self.id,
                'salesorder_extorderid': self.name,
                'salesorder_reference': 'This Order will not be sent to Pubble',
            }
            res = self.env['sofrom.odooto.pubble'].sudo().create(vals)
        else:
            vals = {
                    'transmission_id': self.env['sofrom.odooto.pubble'].get_next_ref(),
                    'sale_order_id': self.id,
                    'salesorder_extorderid': self.name,
                    'salesorder_reference': 'Subject:' + str(self.opportunity_subject or '') + '\n' +
                                            'Order Nr.:' + str(self.name or ''),
                    'salesorder_createdby': self.user_id.email,
                    'salesorder_debtor_extaccountingid': self.published_customer.ref,
                    'salesorder_debtor_extdebtorid': self.published_customer.ref,
                    'salesorder_debtor_addedby': self.published_customer.user_id.email,
                    'salesorder_debtor_addeddate': self.published_customer.create_date,
                    'salesorder_debtor_city' : self.published_customer.city,
                    'salesorder_debtor_emailadres' : self.published_customer.email,
                    'salesorder_debtor_lastmodified' : self.published_customer.write_date,
                    'salesorder_debtor_name' : self.published_customer.name,
                    'salesorder_debtor_postalcode' : self.published_customer.zip,
                    'salesorder_agency' : self.advertising_agency,
                    'salesorder_agency_extaccountingid' : self.advertising_agency.ref,
                    'salesorder_agency_extdebtorid' : self.advertising_agency.ref,
                    'salesorder_agency_addeddate' : self.advertising_agency.create_date,
                    'salesorder_agency_city' : self.advertising_agency.city,
                    'salesorder_agency_emailadres' : self.advertising_agency.email,
                    'salesorder_agency_lastmodified' : self.advertising_agency.write_date,
                    'salesorder_agency_name' : self.advertising_agency.name,
                    'salesorder_agency_postalcode' : self.advertising_agency.zip
            }
            res = self.env['sofrom.odooto.pubble'].sudo().create(vals)
            for line in self.order_line:
                if line.line_pubble_allow:
                    if int(line.product_uom_qty) == 0:
                        del_param = False
                    lvals = {
                            'order_id': res.id,
                            'odoo_order_line': line.id,
                            'ad_adsize_adtypename': line.ad_class.name,
                            'ad_adsize_extadsizeid': line.product_id.default_code,
                            'ad_adsize_height': line.product_uom_qty if line.product_uom.name == 'mm' else line.product_template_id.height,
                            'ad_adsize_name': line.analytic_tag_ids.name or '',
                            'ad_adsize_width': line.product_template_id.width,
                            'ad_edition_editiondate': line.adv_issue.issue_date,
                            'ad_edition_extpublicationid': line.title.name,
                            'ad_extplacementid': line.id,
                            'ad_price': 0,
                            'ad_productiondetail_color': True,
                            'ad_productiondetail_isclassified': False,
                            'ad_productiondetail_dtpcomments': line.layout_remark,
                            'ad_productiondetail_placementcomments': 'External Reference:' + str(line.ad_number or '') + '\n' +
                                                                     'Material Reference:' + str(line.page_reference or '') + '\n' +
                                                                     'Material URL:' + str(line.url_to_material or '') + '\n' +
                                                                     'Product Name:' + line.product_template_id.name_get()[0][1],
                            'ad_status': del_param,
                    }
                    self.env['soline.from.odooto.pubble'].sudo().create(lvals)

        return res

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"


    @api.depends('ad_class', 'adv_issue')
    def _compute_allowed(self):
        for line in self.filtered('advertising'):
            res = False
            if line.ad_class and line.adv_issue.medium.pubble:
                res = True
            line.line_pubble_allow = res


    pubble_sent = fields.Boolean('Order Line sent to Pubble')
    line_pubble_allow = fields.Boolean(compute='_compute_allowed', string='Pubble Allowed', store=True)

    @api.multi
    def write(self, vals):
        res = super(SaleOrderLine, self).write(vals)
        for order in self.mapped('order_id').filtered(lambda s: s.order_pubble_allow and s.advertising):
            if self.advertising and ('product_template_id' or 'adv_issue' or 'product_uom_qty' or 'layout_remark' or 'name') in vals:
                order.action_pubble('update')
        return res


class SofromOdootoPubble(models.Model):
    _name = 'sofrom.odooto.pubble'
    _order = 'create_date desc'

    @api.multi
    def get_next_ref(self):
        return self.env['ir.sequence'].next_by_code('pubble.itf')

    transmission_id = fields.Char(string='Transmission ID', store=True, size=16, readonly=True)
    pubble_so_line = fields.One2many('soline.from.odooto.pubble', 'order_id', string='Order Lines', copy=True)
    pubble_response = fields.Text('Pubble Response')
    sale_order_id = fields.Many2one('sale.order',string='Sale Order')
    salesorder_extorderid = fields.Char(string='Sale Order ID')
    salesorder_reference = fields.Char(string='Opportunity Subject', size=64)
    salesorder_createdby = fields.Char(string='User Name', size=32)
    salesorder_debtor_extaccountingid = fields.Char(string='Advertiser Number')
    salesorder_debtor_extdebtorid = fields.Char(string='Advertiser Number')
    salesorder_debtor_addedby = fields.Char(string='Advertiser Added by', size=32)
    salesorder_debtor_addeddate = fields.Datetime(string='Advertiser Date Added')
    salesorder_debtor_city = fields.Char(string='Advertiser City', size=64)
    salesorder_debtor_emailadres = fields.Char(string='Advertiser Email', size=64)
    salesorder_debtor_lastmodified = fields.Datetime(string='Advertiser Date Last Modified')
    salesorder_debtor_name = fields.Char(string='Advertiser Name', size=64)
    salesorder_debtor_postalcode = fields.Char(string='Advertiser Zip Code', size=32)
    salesorder_agency = fields.Boolean(string='Agency')
    salesorder_agency_extaccountingid = fields.Char(string='Agency Number')
    salesorder_agency_extdebtorid = fields.Char(string='Agency Number')
    salesorder_agency_addeddate = fields.Datetime(string='Agency Date Added')
    salesorder_agency_city = fields.Char(string='Agency City', size=64)
    salesorder_agency_emailadres = fields.Char(string='Agency Email', size=64)
    salesorder_agency_lastmodified = fields.Datetime(string='Agency Date Last Modified')
    salesorder_agency_name = fields.Char(string='Agency Name', size=64)
    salesorder_agency_postalcode = fields.Char(string='Agency Zip Code', size=32)

    @job
    def call_wsdl(self):
        self.ensure_one()
        if self.pubble_response and self.pubble_response == 'True':
            raise UserError(_('This Sale Order already has been succesfully sent to Pubble.'))
        transmissionID = int(float(self.transmission_id))
        client = Client("https://ws.pubble.nl/Sales.svc?singleWsdl")
        SalesOrder = client.factory.create('ns1:salesOrder')
        publisher = "testbdudata"
        apiKey = "9tituo3t2qo4zk7emvlb"


        SalesOrder.extOrderID = int(float(self.salesorder_extorderid))
        SalesOrder.reference = self.salesorder_reference
        SalesOrder.createdBy = self.salesorder_createdby
        SalesOrder.debtor.extAccountingID = int(float(self.salesorder_debtor_extaccountingid))
        SalesOrder.debtor.extDebtorID = int(float(self.salesorder_debtor_extdebtorid))
        SalesOrder.debtor.addedBy = self.salesorder_debtor_addedby
        SalesOrder.debtor.addedDate = datetime.datetime.strptime(self.salesorder_debtor_addeddate,'%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%dT%H:%M:%S.%f')
        SalesOrder.debtor.city = self.salesorder_debtor_city
        SalesOrder.debtor.emailadres = self.salesorder_debtor_emailadres
        SalesOrder.debtor.lastModified = datetime.datetime.strptime(self.salesorder_debtor_lastmodified,'%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%dT%H:%M:%S.%f')
        SalesOrder.debtor.name = self.salesorder_debtor_name
        SalesOrder.debtor.postalcode = self.salesorder_debtor_postalcode
        if not self.salesorder_agency:
            SalesOrder.agency = None
        else:
            SalesOrder.agency.extAccountingID = int(float(self.salesorder_agency_extaccountingid))
            SalesOrder.agency.extDebtorID = int(float(self.salesorder_agency_extdebtorid))
            SalesOrder.agency.addedDate = datetime.datetime.strptime(self.salesorder_agency_addeddate,'%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%dT%H:%M:%S.%f')
            SalesOrder.agency.city = self.salesorder_agency_city
            SalesOrder.agency.emailadres = self.salesorder_agency_emailadres
            SalesOrder.agency.lastModified = datetime.datetime.strptime(self.salesorder_agency_lastmodified,'%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%dT%H:%M:%S.%f')
            SalesOrder.agency.name = self.salesorder_agency_name
            SalesOrder.agency.postalcode = self.salesorder_agency_postalcode

        for line in self.pubble_so_line:
            ad = client.factory.create('ns1:adPlacement')
            ad.adSize.adTypeName = line.ad_adsize_adtypename
            ad.adSize.extAdSizeID = int(float(line.ad_adsize_extadsizeid))
            ad.adSize.height = int(float(line.ad_adsize_height))
            ad.adSize.name = line.ad_adsize_name
            ad.adSize.width = int(float(line.ad_adsize_width))
            ad.edition.editionDate = datetime.datetime.strptime(line.ad_edition_editiondate, '%Y-%m-%d').strftime('%Y-%m-%dT%H:%M:%S.%f')
            ad.edition.extPublicationID = line.ad_edition_extpublicationid
            ad.extPlacementID = int(float(line.ad_extplacementid))
            ad.price = 0
            ad.productionDetail.color = "true" if line.ad_productiondetail_color else "false"
            ad.productionDetail.isClassified = "true" if line.ad_productiondetail_isclassified else "false"
            ad.productionDetail.dtpComments = line.ad_productiondetail_dtpcomments
            ad.productionDetail.placementComments = line.ad_productiondetail_placementcomments
            ad.status = "active" if line.ad_status else "deleted"

            SalesOrder.orderLine_Ads.adPlacement.append(ad)
#        print SalesOrder
        response = client.service.processOrder(SalesOrder, transmissionID, publisher, apiKey)
        self.write({'pubble_response': response})
        if response == True:
            self.env['sale.order'].search([('id','=',self.sale_order_id.id)]).write({'date_sent_pubble': datetime.datetime.now()})
#            for line in self.pubble_so_line:
#                self.env['sale.order.line'].search([('id', '=', line.ad_extplacementid)]).write({'pubble_sent': True})

        return True


class SoLinefromOdootoPubble(models.Model):
    _name = 'soline.from.odooto.pubble'


    order_id = fields.Many2one('sofrom.odooto.pubble', string='Order Reference', required=True, ondelete='cascade', index=True, copy=False)
    odoo_order_line = fields.Many2one('sale.order.line', string='Order Line Reference', required=True, index=True, copy=False)
    ad_adsize_adtypename = fields.Char(string='Advertising Class Name', size=64)
    ad_adsize_extadsizeid = fields.Char(string='Product ID')
    ad_adsize_height = fields.Integer(string='Height mm')
    ad_adsize_name = fields.Char(string='Advertising Product Name', size=64)
    ad_adsize_width = fields.Integer(string='Width mm')
    ad_edition_editiondate = fields.Date(string='Issue Date')
    ad_edition_extpublicationid = fields.Char(string='Advertising Title Name', size=64)
    ad_extplacementid = fields.Integer(string='Line ID')
    ad_price = fields.Integer(string='Price', default=0)
    ad_productiondetail_color = fields.Boolean(string='Color')
    ad_productiondetail_isclassified = fields.Boolean(string='Classified')
    ad_productiondetail_dtpcomments = fields.Text(string='Layout Remarks')
    ad_productiondetail_placementcomments = fields.Text(string='Placement Remarks')
    ad_status = fields.Boolean(string='Active')

