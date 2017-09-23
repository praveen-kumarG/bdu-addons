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


class SaleOrder(models.Model):
    _inherit = ["sale.order"]

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('submitted', 'Submitted for Approval'),
        ('approved1', 'Approved by Sales Mgr'),
        ('pubble', 'Sent to Pubble'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sale Order'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
    date_sent_pubble = fields.Date('Date order sent to Pubble', index=True,
                                    help="Date on which sales order is sent to Pubble.")

    @api.multi
    def action_pubble(self):
        self.transfer_order_to_pubble()
        return self.write({'state': 'pubble',
                           'date_sent_pubble': fields.Date.context_today(self)})

    def transfer_order_to_pubble(self):
        client = Client("file:///workspace/SalesWebService [13-9-2017].wsdl")
        SalesOrder = client.factory.create('ns1:salesOrder')
        transmissionID = 257018651
        publisher = "testbdudata"
        apiKey = "9tituo3t2qo4zk7emvlb"
        SalesOrder.extOrderID = self.name
        SalesOrder.reference = self.opportunity_subject
        SalesOrder.createdBy = self.user_id.name
        SalesOrder.debtor.extAccountingID = self.published_customer.ref
        SalesOrder.debtor.extDebtorID = self.published_customer.ref
        SalesOrder.debtor.addedDate = self.published_customer.create_date
        SalesOrder.debtor.city = self.published_customer.city
        SalesOrder.debtor.emailadres = self.published_customer.email
        SalesOrder.debtor.lastModified = self.published_customer.write_date
        SalesOrder.debtor.name = self.published_customer.name
        SalesOrder.debtor.postalcode = self.published_customer.zip
        if not self.advertising_agency:
            SalesOrder.agency = None
        else:
            SalesOrder.agency.extAccountingID = self.advertising_agency.ref
            SalesOrder.agency.extDebtorID = self.advertising_agency.ref
            SalesOrder.agency.addedDate = self.advertising_agency.create_date
            SalesOrder.agency.city = self.advertising_agency.city
            SalesOrder.agency.emailadres = self.advertising_agency.email
            SalesOrder.agency.lastModified = self.advertising_agency.write_date
            SalesOrder.agency.name = self.advertising_agency.name
            SalesOrder.agency.postalcode = self.advertising_agency.zip
        for line in self.order_line:
            ad += 1
            ad = client.factory.create('ns1:adPlacement')
            ad.adSize.adTypeName = "Advertentiepagina"
            ad.adSize.extAdSizeID = 4005
            ad.adSize.height = 200
            ad.adSize.name = "KWARTADVVP"
            ad.adSize.width = 522
            ad.edition.editionDate = "2017-09-27T00:00:00"
            ad.edition.extPublicationID = line.title
            ad.extPlacementID = 14890147
            ad.price = 0
            ad.productionDetail.color = "true"
            ad.productionDetail.isClassified = "false"
            ad.productionDetail.dtpComments = line.layout_remark
            ad.productionDetail.placementComments = line.name
            ad.status = "active"
            SalesOrder.orderLine_Ads.adPlacement.append(ad)

        response = client.service.processOrder(SalesOrder, transmissionID, publisher, apiKey)
        return True