# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
import logging

import os
import base64
import xml.etree.ElementTree as ET
from collections import defaultdict


_logger = logging.getLogger(__name__)


class Job(models.Model):
    _name = "wobe.job"
    _inherit = ['mail.thread']
    _description = 'WOBE Job'

    job_ref = fields.Char('WOBE Job #', help='XML reference', required=True, index=True)
    bduorder_ref = fields.Char('BDUOrder #', help='BDUOrder reference', required=True, index=True)
    name = fields.Char('Name', help='BDUOrder reference', required=True, index=True)

    title = fields.Char('Newspaper Title')
    issue_date = fields.Date('Issue Date')
    total_pages = fields.Integer('Total Pages')
    strook = fields.Char('Strook')
    plate_type = fields.Selection([('PA', 'PA'), ('PU', 'PU')], string='Plate Type')
    plate_amount = fields.Integer('Plate Amount')

    production_start = fields.Datetime('Production Start', help='Info DateTime Start')
    production_stop = fields.Datetime('Production End', help='Info DateTime End')

    planned_quantity = fields.Integer('Production Amount')
    gross_quantity = fields.Integer('Gross Qty', help='Prints Gross')
    net_quantity = fields.Integer('Net Qty', help='Prints Net')

    paper_mass_1 = fields.Integer('Paper Mass 01', help='Used Gram01')
    paper_mass_2 = fields.Integer('Paper Mass 02', help='Used Gram02')
    paper_mass_3 = fields.Integer('Paper Mass 03', help='Used Gram03')
    paper_mass_4 = fields.Integer('Paper Mass 04', help='Used Gram04')
    paper_mass_5 = fields.Integer('Paper Mass 05', help='Used Gram05')
    paper_mass_6 = fields.Integer('Paper Mass 06', help='Used Gram06')
    paper_mass_7 = fields.Integer('Paper Mass 07', help='Used Gram07')

    paper_width_1 = fields.Integer('Paper Width 01', help='Used WebWidth01')
    paper_width_2 = fields.Integer('Paper Width 02', help='Used WebWidth02')
    paper_width_3 = fields.Integer('Paper Width 03', help='Used WebWidth03')
    paper_width_4 = fields.Integer('Paper Width 04', help='Used WebWidth04')
    paper_width_5 = fields.Integer('Paper Width 05', help='Used WebWidth05')
    paper_width_6 = fields.Integer('Paper Width 06', help='Used WebWidth06')
    paper_width_7 = fields.Integer('Paper Width 07', help='Used WebWidth07')

    waste_start = fields.Integer('Waste Start')
    waste_total = fields.Integer('Waste Total')

    booklet_ids = fields.One2many('wobe.booklet', 'job_id', 'Booklets', copy=True)

    xmlfile_1 = fields.Binary('XML File1', help='Imported XML File 1')
    filename1 = fields.Char()
    xmlfile_3 = fields.Binary('XML File3', help='Imported XML File 1')
    filename3 = fields.Char()
    xmlfile_4 = fields.Binary('XML File4', help='Imported XML File 4')
    filename4 = fields.Char()


    state = fields.Selection([('new', 'New'),
                             ('order_created', 'Order Created'),
                             ('exception', 'Exception')], string='Status', default='new',
                             copy=False, required=True, track_visibility='onchange')

    order_id = fields.Many2one('sale.order', string='Sale Order', ondelete='restrict', help='Associated Sale Order')


    @api.multi
    def read_xml_file(self):
        path = self._context.get('local_path', '')

        dir_toRead = os.path.join(path, 'To_read')
        dir_Read   = os.path.join(path, 'Read')
        dir_Error  = os.path.join(path, 'Error')
        try:
            os.listdir(dir_toRead) and os.listdir(dir_Read) and os.listdir(dir_Error)
        except Exception, e:
            _logger.exception("Wobe Import File : %s" % str(e))
            return False

        Job_obj = self.env['wobe.job']
        newJobs = self.env['wobe.job']

        groupedFiles = defaultdict(lambda: {'file1': False, 'file3': False, 'file4':False})
        partialFiles = []
        part1, part3, part4 = {}, {}, {}

        for filename in os.listdir(dir_toRead):
            if not filename.endswith('.xml'): continue
            File = os.path.join(dir_toRead, filename)

            try:
                tree = ET.parse(File)
                root = tree.getroot()
                header = root.attrib

                if header.get('SenderId') == 'WOBEWebportal' and header.get('Type') == 'CreateJob':
                    BDUOrder = root.find('Newspaper').find('BduOrderId').text
                    part1[BDUOrder] = filename

                elif header.get('SenderId') == 'WOBEWorkflow' and header.get('Type') == 'PlatesUsed':
                    BDUOrder = root.find('Newspaper').find('BduOrderId').text
                    JobId    = root.find('Newspaper').find('WobeJobId').text.split(':')[2]
                    part3[(BDUOrder, JobId)] = filename

                elif header.get('{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation') == 'kba_reportdata.xsd':
                    JobId = root.find('info_jobid').text
                    part4[JobId] = filename

            except:
                # Move to 'Error' folder
                tomove = os.path.join(dir_Error, filename)
                os.rename(File, tomove)

        # Files are linked & grouped:
        for k1, f1 in part1.iteritems():
            key, f3, f4 = False, False, False

            for k3, f3 in part3.iteritems():
                key = k3
                if k1 == k3[0]:
                    break

            for k4, f4 in part4.iteritems():
                if k4 == k3[1]:
                    break

            if not (key and f3 and f4):
                partialFiles.append(f1)
                if f3: partialFiles.append(f3)
                if f4: partialFiles.append(f4)
                continue

            groupedFiles[key] = {'file1': f1, 'file3': f3, 'file4': f4}


        for key, fv in groupedFiles.iteritems():
            File1 = os.path.join(dir_toRead, fv['file1'])
            File3 = os.path.join(dir_toRead, fv['file3'])
            File4 = os.path.join(dir_toRead, fv['file4'])

            try:
                job = Job_obj.search([('job_ref', '=', key[1])])
                if job: continue

                tree1 = ET.parse(File1)
                root1 = tree1.getroot()
                data1 = root1.find('Newspaper')

                tree3 = ET.parse(File3)
                root3 = tree3.getroot()
                data3 = root3.find('Newspaper')

                tree4 = ET.parse(File4)
                data4 = tree4.getroot()

                vals = self._prepare_job_data(data1, data3, data4)

                fn = open(File1, 'r')
                vals.update({'filename1': fv['file1'], 'xmlfile_1': base64.encodestring(fn.read()),})
                fn.close()

                fn = open(File3, 'r')
                vals.update({'filename3': fv['file3'], 'xmlfile_3': base64.encodestring(fn.read()),})
                fn.close()

                fn = open(File4, 'r')
                vals.update({'filename4': fv['file4'], 'xmlfile_4': base64.encodestring(fn.read()),})
                fn.close()

                job = Job_obj.create(vals)
                newJobs += job

                # Move to 'Read' folder
                tomove = os.path.join(dir_Read, fv['file1'])
                os.rename(File1, tomove)
                tomove = os.path.join(dir_Read, fv['file3'])
                os.rename(File3, tomove)
                tomove = os.path.join(dir_Read, fv['file4'])
                os.rename(File4, tomove)

            except:
                # Move to 'Error' folder
                tomove = os.path.join(dir_Error, fv['file1'])
                os.rename(File1, tomove)
                tomove = os.path.join(dir_Error, fv['file3'])
                os.rename(File3, tomove)
                tomove = os.path.join(dir_Error, fv['file4'])
                os.rename(File4, tomove)

        # Partial / Incomplete Files
        # Move to 'Error' folder
        for pf in partialFiles:
            File = os.path.join(dir_toRead, pf)
            tomove = os.path.join(dir_Error, pf)
            os.rename(File, tomove)

        return newJobs.action_create_order()


    @api.multi
    def _prepare_job_data(self, data1, data3, data4):
        res = {}

        Plates = data3.find('PlatesUsed')

        res = {
            'job_ref' : data1.find('WobeJobId').text,
            'bduorder_ref': data1.find('BduOrderId').text,
            'name'    : data1.find('BduOrderId').text,
            'title'   : data1.find('NewspaperTitle').text,

            'issue_date' : data1.find('IssueDate').text,
            'total_pages': int(data1.find('TotalPages').text or 0),
            'strook': data1.find('Strook').text,
            'planned_quantity': int(data1.find('ProductionAmount').text or 0),

            'plate_type'  : Plates.find('PlateType').text,
            'plate_amount': int(Plates.find('PlateAmount').text or 0),

            'production_start' : data4.find('info_datetime_start').text,
            'production_stop'  : data4.find('info_datetime_end').text,
            'gross_quantity'   : int(data4.find('prints_gross').text or 0),
            'net_quantity'     : int(data4.find('prints_net').text or 0),

            'paper_mass_1'  : int(data4.find('used_gram01').text or 0),
            'paper_mass_2'  : int(data4.find('used_gram02').text or 0),
            'paper_mass_3'  : int(data4.find('used_gram03').text or 0),
            'paper_mass_4'  : int(data4.find('used_gram04').text or 0),
            'paper_mass_5'  : int(data4.find('used_gram05').text or 0),
            'paper_mass_6'  : int(data4.find('used_gram06').text or 0),
            'paper_mass_7'  : int(data4.find('used_gram07').text or 0),

            'paper_width_1'  : int(data4.find('used_webwidth01').text or 0),
            'paper_width_2'  : int(data4.find('used_webwidth02').text or 0),
            'paper_width_3'  : int(data4.find('used_webwidth03').text or 0),
            'paper_width_4'  : int(data4.find('used_webwidth04').text or 0),
            'paper_width_5'  : int(data4.find('used_webwidth05').text or 0),
            'paper_width_6'  : int(data4.find('used_webwidth06').text or 0),
            'paper_width_7'  : int(data4.find('used_webwidth07').text or 0),

            'waste_start' : int(data4.find('waste_start').text or 0),
            'waste_total' : int(data4.find('waste_total').text or 0),

               }

        lines = []
        for booklet in data1.iter('Booklet'):
            lnvals = {
                'booklet_ref': booklet.get('id'),
                'pages' : booklet.find('Pages').text,
                'format': booklet.find('Format').text,
                'page_weight': booklet.find('PaperWeight').text,

                'stitching': True if booklet.find('Stitching').text == 'Yes' else False,
                'glueing'  : True if booklet.find('Glueing').text == 'Yes' else False,
            }
            lines.append(lnvals)

        res['booklet_ids'] = map(lambda x:(0,0,x), lines)

        return res


    @api.multi
    def action_create_order(self):
        sale_obj = self.env['sale.order']

        for case in self:
            if case.order_id: continue

            vals = case._prepare_order_data()
            if vals:
                order = sale_obj.create(vals)
                order.message_post_with_view('mail.message_origin_link',
                    values={'self': order, 'origin': case},
                    subtype_id=self.env.ref('mail.mt_note').id)

                case.write({'state': 'order_created', 'order_id': order.id})
            else:
                case.write({'state': 'exception'})

        return True


    @api.multi
    def _prepare_order_data(self):
        self.ensure_one()

        aa = self.env['account.analytic.account'].search([('name','=', self.title)])
        partner = aa and aa.partner_id or False
        prodTem_obj = self.env['product.template']
        product_obj = self.env['product.product']
        sale_obj = self.env['sale.order']
        variant_obj = self.env['product.attribute.value']

        if not aa:
            self.message_post(body=_('Analytic Account not found for this NewspaperTitle.'))
            return {}

        elif not partner:
            self.message_post(body=_('Partner not mapped for this NewspaperTitle.'))
            return {}

        res = sale_obj.default_get(['date_order'])
        res.update({
            'client_order_ref': self.bduorder_ref,
            'project_id': aa.id,
            'partner_id': partner.id,
            'date_order': self.issue_date or res['date_order'],
               })

        def _get_linevals(productID, qty=1):
            return {
                'product_id': productID,
                'product_uom_qty': qty * ((self.net_quantity / 1000) or 1),
            }

        lines = []
        strook = glueing = stitching = False
        glueCnt = stitchCnt = 0
        for p in product_obj.search([('print_category','in', ('strook', 'stitching', 'glueing'))]):
            if p.print_category   == 'strook'   : strook = p.id
            elif p.print_category == 'glueing'  : glueing = p.id
            elif p.print_category == 'stitching': stitching = p.id

        pFormat = self.env.ref('wobe_imports.variant_attribute_1', False)
        pPages  = self.env.ref('wobe_imports.variant_attribute_2', False)
        pWeight = self.env.ref('wobe_imports.variant_attribute_3', False)

        emsg = ''
        if not pFormat: emsg += "Paper Format, "
        if not pPages : emsg += "Paper Pages, "
        if not pWeight: emsg += "Paper Weight."
        if emsg:
            self.message_post(body=_("Variant Attributes not found for %s"%emsg))
            return {}

        # Strook:
        if self.strook == 'Ja':
            if not strook:
                self.message_post(body=_("Product not found for the print-category : 'Strook'"))
                return {}

            lnvals = _get_linevals(strook)
            lines.append(lnvals)

        for booklet in self.booklet_ids:
            if booklet.glueing: glueCnt += 1
            if booklet.stitching: stitchCnt += 1

            v1 = variant_obj.search([('name','=', booklet.pages), ('attribute_id','=', pPages.id)])
            v2 = variant_obj.search([('name','=', booklet.format), ('attribute_id','=', pFormat.id)])
            v3 = variant_obj.search([('name','=', booklet.page_weight), ('attribute_id','=', pWeight.id)])

            product = product_obj.search([('attribute_value_ids', 'in', v1.ids),
                                          ('attribute_value_ids', 'in', v2.ids),
                                          ('attribute_value_ids', 'in', v3.ids)], order='id desc', limit=1)
            # Booklet-Product
            if product:
                lines.append(_get_linevals(product.ids[0]))
            else:
                body = _("Product not found for this variants 'Pages: %s', 'Format: %s', 'Paper Weight: %s'!!"
                          %(str(booklet.pages), booklet.format, booklet.page_weight))
                self.message_post(body=body)
                return {}

        # Glueing:
        if glueCnt:
            if not stitching:
                self.message_post(body=_("Product not found for the print-category : 'Stitching'"))
                return {}
            lines.append(_get_linevals(glueing, qty=glueCnt))

        # Stitching:
        if stitchCnt:
            if not glueing:
                self.message_post(body=_("Product not found for the print-category : 'Glueing'"))
                return {}
            lines.append(_get_linevals(stitching, qty=stitchCnt))

        res['order_line'] = map(lambda x:(0,0,x), lines)

        return res


class Booklet(models.Model):
    _name = "wobe.booklet"
    _description = 'WOBE Booklet'
    _rec_name = 'booklet_ref'

    job_id = fields.Many2one('wobe.job', required=True, ondelete='cascade', index=True, copy=False)
    booklet_ref = fields.Char('Booklet Ref', help='XML reference', required=True, index=True)

    pages = fields.Char('Pages')
    format = fields.Char('Format')
    page_weight = fields.Char('Page Weight')
    stitching = fields.Boolean('Stitching', default=False)
    glueing = fields.Boolean('Glueing', default=False)