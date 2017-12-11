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
    _inherit = ['mail.thread','ir.needaction_mixin']
    _description = 'WOBE Job'

    @api.one
    @api.depends('edition_ids')
    def _compute_all(self):
        self.waste_start = sum(line.waste_start for line in self.edition_ids)
        self.waste_total = sum(line.waste_total for line in self.edition_ids)
        self.plate_amount = sum(line.plate_amount for line in self.edition_ids)
        self.gross_quantity = sum(line.gross_quantity for line in self.edition_ids)
        self.net_quantity = sum(line.net_quantity for line in self.edition_ids)

        self.production_start = min(line.production_start for line in self.edition_ids)
        self.production_stop = max(line.production_stop for line in self.edition_ids)


    job_ref = fields.Char('WOBE Job #', help='XML reference', required=True, index=True)
    bduorder_ref = fields.Char('BDUOrder #', help='BDUOrder reference', required=True, index=True)
    name = fields.Char('Name', help='BDUOrder reference', required=True, index=True)

    title = fields.Char('Newspaper Title')
    issue_date = fields.Date('Issue Date')
    total_pages = fields.Integer('Total Pages')
    strook = fields.Char('Strook')
    plate_type = fields.Selection([('PA', 'PA'), ('PU', 'PU')], string='Plate Type')
    plate_amount = fields.Integer(compute=_compute_all, string='Plate Amount', store=True)

    production_start = fields.Char(compute=_compute_all, string='Production Start', help='Info DateTime Start', store=True)
    production_stop = fields.Char(compute=_compute_all, string='Production End', help='Info DateTime End', store=True)

    planned_quantity = fields.Integer('Production Amount')
    gross_quantity = fields.Integer(compute=_compute_all, string='Gross Qty', help='Prints Gross', store=True)
    net_quantity = fields.Integer(compute=_compute_all, string='Net Qty', help='Prints Net', store=True)

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

    waste_start = fields.Integer(compute=_compute_all, string='Waste Start', store=True)
    waste_total = fields.Integer(compute=_compute_all, string='Waste Total', store=True)

    booklet_ids = fields.One2many('wobe.booklet', 'job_id', 'Booklets', copy=True)
    edition_ids = fields.One2many('wobe.edition', 'job_id', 'Editions', copy=True)

    state = fields.Selection([('new', 'New'), ('waiting', 'Waiting'),
                             ('order_created', 'Order Created'),
                             ('exception', 'Exception')], string='Status', default='new',
                             copy=False, required=True, track_visibility='onchange')

    order_id = fields.Many2one('sale.order', string='Sale Order', ondelete='restrict', help='Associated Sale Order')
    company_id = fields.Many2one('res.company', 'Company')


    @api.model
    def _needaction_domain_get(self):
        return [('state', '=', 'exception')]

    @api.multi
    def read_xml_file(self):
        path = self._context.get('local_path', '')
        companyID = self._context.get('company_id', '')

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
        Attachment = self.env['ir.attachment']

        groupedFiles = defaultdict(lambda: {'file1': False, 'file3N4': {}})
        part1, part3, part4 = {}, {}, {}

        # --------------------------
        # Files identified
        # --------------------------
        for filename in os.listdir(dir_toRead):
            if not filename.endswith('.xml'): continue
            File = os.path.join(dir_toRead, filename)

            try:
                tree = ET.parse(File)
                root = tree.getroot()
                header = root.attrib

                if header.get('SenderId') == 'WOBEWebportal' and header.get('Type') == 'CreateJob':
                    BDUOrder = root.find('Newspaper').find('BduOrderId').text
                    edCnt = len(root.find('Newspaper').findall('Edition'))
                    part1[BDUOrder] = [filename, edCnt]

                elif header.get('SenderId') == 'WOBEWorkflow' and header.get('Type') == 'PlatesUsed':
                    BDUOrder = root.find('Newspaper').find('BduOrderId').text
                    KBAJobId = root.find('Newspaper').find('WobeJobId').text.split(':')[2]
                    if not BDUOrder in part3:
                        part3[BDUOrder] = {KBAJobId: filename}
                    else:
                        part3[BDUOrder].update({KBAJobId: filename})

                elif header.get('{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation') == 'kba_reportdata.xsd':
                    KBAJobId = root.find('info_jobid').text
                    part4[KBAJobId] = filename

            except:
                # Move to 'Error' folder
                tomove = os.path.join(dir_Error, filename)
                os.rename(File, tomove)

        # -----------------------------
        # Files are linked & grouped:
        # -----------------------------
        for key in set(part1).intersection(set(part3)):
            file1 = part1[key][0]
            editionCnt = part1[key][1]

            map3N4 = {}
            for y in set(part3[key]).intersection(set(part4)):
                f3, f4 = part3[key][y], part4[y]
                map3N4[f3] = f4

            # EditionCount check
            if editionCnt == len(map3N4):
                groupedFiles[key] = {'file1': file1, 'file3N4': map3N4}


        # --------------------------
        # Extract Data & Create job
        # --------------------------
        for key, fv in groupedFiles.iteritems():
            File1 = os.path.join(dir_toRead, fv['file1'])

            try:
                job = Job_obj.search([('bduorder_ref', '=', key)])
                if job: continue

                tree1 = ET.parse(File1)
                root1 = tree1.getroot()
                data1 = root1.find('Newspaper')

                edData = {}
                for file3, file4 in fv['file3N4'].iteritems():
                    File3 = os.path.join(dir_toRead, file3)
                    File4 = os.path.join(dir_toRead, file4)

                    tree3 = ET.parse(File3)
                    root3 = tree3.getroot()
                    data3 = root3.find('Newspaper')

                    tree4 = ET.parse(File4)
                    data4 = tree4.getroot()

                    edData.update(self._extract_EditionData(edData, data3, data4))

                vals = self._prepare_job_data(data1, edData)
                vals['company_id'] = companyID or self.env.user.company_id.id

                job = Job_obj.create(vals)
                newJobs += job

                # Original Files
                fn = open(File1, 'r')
                Attachment.sudo().create({
                        'name': fv['file1'], 'datas_fname': fv['file1'],
                        'datas': base64.encodestring(fn.read()),
                        'res_model': self._name, 'res_id': job.id})
                fn.close()

                for fileN in fv['file3N4'].keys() + fv['file3N4'].values():
                    FileN = os.path.join(dir_toRead, fileN)

                    fn = open(FileN, 'r')
                    Attachment.sudo().create({
                            'name': fileN, 'datas_fname': fileN,
                            'datas': base64.encodestring(fn.read()),
                            'res_model': self._name, 'res_id': job.id})
                    fn.close()

                # Move to 'Read' folder
                tomove = os.path.join(dir_Read, fv['file1'])
                os.rename(File1, tomove)

                for file3, file4 in fv['file3N4'].iteritems():
                    File3 = os.path.join(dir_toRead, file3)
                    File4 = os.path.join(dir_toRead, file4)

                    tomove = os.path.join(dir_Read, file3)
                    os.rename(File3, tomove)
                    tomove = os.path.join(dir_Read, file4)
                    os.rename(File4, tomove)

            except:
                # Move to 'Error' folder
                tomove = os.path.join(dir_Error, fv['file1'])
                os.rename(File1, tomove)

                for file3, file4 in fv['file3N4'].iteritems():
                    File3 = os.path.join(dir_toRead, file3)
                    File4 = os.path.join(dir_toRead, file4)

                    tomove = os.path.join(dir_Error, file3)
                    os.rename(File3, tomove)
                    tomove = os.path.join(dir_Error, file4)
                    os.rename(File4, tomove)

        return newJobs.action_create_order()


    @api.multi
    def _prepare_job_data(self, data1, edData):
        res = {}
        edlines, lines = [], []

        editionInfoL = ['plate_amount', 'net_quantity', 'gross_quantity', 'net_quantity',
                        'production_start', 'production_stop', 'waste_start', 'waste_total']

        commonInfoL = ['plate_type',
                       'paper_mass_1', 'paper_mass_2', 'paper_mass_3', 'paper_mass_4', 'paper_mass_5',
                       'paper_mass_6', 'paper_mass_7',
                       'paper_width_1', 'paper_width_2', 'paper_width_3', 'paper_width_4', 'paper_width_5',
                       'paper_width_6', 'paper_width_7']

        # Edition Lines
        for key, val in edData.iteritems():

            elnvals = {'name' : key }
            for x in editionInfoL:
                elnvals[x] = val.get(x, False)

            # Note: paper/Other Info
            # remains same for all Editions
            for y in commonInfoL:
                res[y] = val.get(y)

            edlines.append(elnvals)

        # Booklet Lines
        for booklet in data1.iter('Booklet'):
            lnvals = {
                'booklet_ref': booklet.get('id'),
                'pages' : booklet.find('Pages').text,
                'format': booklet.find('Format').text,
                'paper_weight': booklet.find('PaperWeight').text,

                'stitching': True if booklet.find('Stitching').text == 'Yes' else False,
                'glueing'  : True if booklet.find('Glueing').text == 'Yes' else False,
            }
            lines.append(lnvals)


        res.update({
            'job_ref' : data1.find('WobeJobId').text,
            'bduorder_ref': data1.find('BduOrderId').text,
            'name'    : data1.find('BduOrderId').text,
            'title'   : data1.find('NewspaperTitle').text,

            'issue_date' : data1.find('IssueDate').text,
            'total_pages': int(data1.find('TotalPages').text or 0),
            'strook': data1.find('Strook').text,
            'planned_quantity': int(data1.find('ProductionAmount').text or 0),

            'edition_ids' : map(lambda x:(0,0,x), edlines),
            'booklet_ids' : map(lambda x:(0,0,x), lines),
               })
        return res


    @api.multi
    def _extract_EditionData(self, res, data3, data4):
        ' Data extracted from XMLFile3 & XMLFile4'

        Plates = data3.find('PlatesUsed')
        edName = data4.find('info_product').text

        res[edName] = {
            'plate_type'  : Plates.find('PlateType').text,
            'plate_amount': int(Plates.find('PlateAmount').text or 0),

            'production_start' : data4.find('info_datetime_start').text,
            'production_stop'  : data4.find('info_datetime_end').text,
            'gross_quantity'   : int(data4.find('prints_gross').text or 0),
            'net_quantity'     : int(data4.find('prints_net').text or 0),

            'waste_start' : int(data4.find('waste_start').text or 0),
            'waste_total' : int(data4.find('waste_total').text or 0),

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

               }
        return res


    @api.multi
    def action_create_order(self):
        sale_obj = self.env['sale.order']

        for case in self:
            if case.order_id: continue

            vals = case._prepare_order_data()
            if vals:
                order = sale_obj.create(vals)
                order.action_confirm()
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

        prodTem_obj = self.env['product.template']
        product_obj = self.env['product.product']
        sale_obj = self.env['sale.order']
        variant_obj = self.env['product.attribute.value']
        aa = self.env['account.analytic.account'].search([('name','=', self.title)])
        partner = aa and aa.partner_id or False

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
            'company_id': self.company_id.id,
            'origin': self.bduorder_ref,
               })

        def _get_linevals(productID, qty=1, forceQty=0):
            Qty = qty * ((self.net_quantity / 1000) or 1)

            return {
                'product_id': productID,
                'product_uom_qty': forceQty if forceQty else Qty,
            }

        lines = []
        strook = glueing = stitching = plateChange = pressStop = False
        glueCnt = stitchCnt = 0
        for p in product_obj.search([('print_category','in', ('strook', 'stitching', 'glueing',
                                                              'plate_change', 'press_stop'))]):
            if p.print_category   == 'strook'   : strook = p.id
            elif p.print_category == 'glueing'  : glueing = p.id
            elif p.print_category == 'stitching': stitching = p.id
            elif p.print_category == 'plate_change': plateChange = p.id
            elif p.print_category == 'press_stop'  : pressStop = p.id

        pPages  = self.env.ref('wobe_imports.variant_attribute_2', False)
        pWeight = self.env.ref('wobe_imports.variant_attribute_3', False)

        emsg = ''
        if not pPages : emsg += "Pages, "
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

        booklet_processed_ids = []
        for booklet in self.booklet_ids:
            if booklet.glueing: glueCnt += 1
            if booklet.stitching: stitchCnt += 1
            if booklet.id not in booklet_processed_ids:
                pFormat = 'MP' if booklet.format == 'MAG' else booklet.format
                #search for record in booklet with same format & page weight
                booklet_processed_ids.append(booklet.id)
                search_format = [booklet.format]
                if booklet.format == 'MAG':
                    search_format = ['MAG', 'MP']
                dup_booklet_ids = self.env['wobe.booklet'].search([('id', 'not in', booklet_processed_ids), ('format', 'in', search_format),('paper_weight', '=', booklet.paper_weight)])
                pages = int(booklet.pages)
                for booklet_obj in dup_booklet_ids:
                    booklet_processed_ids.append(booklet_obj.id)
                    pages += int(booklet_obj.pages)
                ###################
                v1 = variant_obj.search([('name','=', str(pages)), ('attribute_id','=', pPages.id)])
                v2 = variant_obj.search([('name','=', booklet.paper_weight), ('attribute_id','=', pWeight.id)])
                product = product_obj.search([('attribute_value_ids', 'in', v1.ids),
                                              ('attribute_value_ids', 'in', v2.ids),
                                              ('print_format_template','=', True),
                                              ('formats','=', pFormat),], order='id desc', limit=1)
                # Booklet-Product
                if product:
                    lines.append(_get_linevals(product.ids[0]))
                else:
                    body = _("Product not found for this variants 'Pages: %s', 'Format: %s', 'Paper Weight: %s'!!"
                              %(str(pages), pFormat, booklet.paper_weight))
                    self.message_post(body=body)
                    return {}
        # Glueing:
        if glueCnt:
            if not glueing:
                self.message_post(body=_("Product not found for the print-category : 'Glueing'"))
                return {}
            lines.append(_get_linevals(glueing, qty=glueCnt))

        # Stitching:
        if stitchCnt:
            if not stitching:
                self.message_post(body=_("Product not found for the print-category : 'Stitching'"))
                return {}
            lines.append(_get_linevals(stitching, qty=stitchCnt))

        # Multiple Editions:
        if len(self.edition_ids) > 1:
            if not plateChange:
                self.message_post(body=_("Product not found for the print-category : 'Plate Change'"))
                return {}

            elif not pressStop:
                self.message_post(body=_("Product not found for the print-category : 'Press Stop'"))
                return {}

            lines.append(_get_linevals(pressStop, forceQty=len(self.edition_ids.ids)-1))
            lines.append(_get_linevals(plateChange, forceQty=(round((self.plate_amount-sum(line.calculated_plates for line in self.booklet_ids))/4.0))))

        res['order_line'] = map(lambda x:(0,0,x), lines)

        return res

    @api.multi
    def action_view_sales(self):
        self.ensure_one()
        action = self.env.ref('sale.action_orders')
        return {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'view_type':  'form' if self.order_id else action.view_type,
            'view_mode': 'form' if self.order_id else action.view_mode,
            'target': action.target,
            'res_id': self.order_id.id or False,
            'res_model': action.res_model,
            'domain': [('id', '=', self.order_id.id)],
        }


class Booklet(models.Model):
    _name = "wobe.booklet"
    _description = 'WOBE Booklet'
    _rec_name = 'booklet_ref'

    job_id = fields.Many2one('wobe.job', required=True, ondelete='cascade', index=True, copy=False)
    booklet_ref = fields.Char('Booklet Ref', help='XML reference', required=True, index=True)

    pages = fields.Char('Pages')
    format = fields.Char('Format')
    paper_weight = fields.Char('Paper Weight')
    stitching = fields.Boolean('Stitching', default=False)
    glueing = fields.Boolean('Glueing', default=False)

    calculated_plates = fields.Float(string='Calculated Plates', store=True, compute='_compute_all', digits=dp.get_precision('Product Unit of Measure'))
    calculated_mass = fields.Float(string='Calculated Mass', store=True, compute='_compute_all', digits=dp.get_precision('Product Unit of Measure'))
    calculated_ink = fields.Float(string='Calculated Ink', store=True, compute='_compute_all', digits=dp.get_precision('Product Unit of Measure'))
    calculated_hours = fields.Float(string='Calculated Hours', store=True, compute='_compute_all', digits=dp.get_precision('Product Unit of Measure'))

    @api.depends('format', 'pages', 'paper_weight')
    def _compute_all(self):
        for booklet in self:
            #calculated_plates
            booklet.calculated_plates = 0.0
            pages = float(booklet.pages)
            paper_weight = float(booklet.paper_weight)
            if pages <= 48.0:
                booklet.calculated_plates = pages * 4
            elif pages > 48.0:
                if booklet.format == 'BS':
                    booklet.calculated_plates = pages * 4
                elif booklet.format == 'TB':
                    booklet.calculated_plates = pages * 2
                elif booklet.format == 'MAG':
                    booklet.calculated_plates = pages

            #calculated_mass
            booklet.calculated_mass = 0.0
            product_obj = self.env['product.product']
            variant_obj = self.env['product.attribute.value']
            pPages = self.env.ref('wobe_imports.variant_attribute_2', False)
            pWeight = self.env.ref('wobe_imports.variant_attribute_3', False)
            v1 = variant_obj.search([('name', '=', booklet.pages), ('attribute_id', '=', pPages.id)])
            v2 = variant_obj.search([('name', '=', booklet.paper_weight), ('attribute_id', '=', pWeight.id)])

            product = product_obj.search([('attribute_value_ids', 'in', v1.ids),
                                          ('attribute_value_ids', 'in', v2.ids),
                                          ('print_format_template', '=', True),
                                          ('formats', '=', booklet.format), ], order='id desc', limit=1)
            if product:
                booklet.calculated_mass = (product.product_tmpl_id.booklet_surface_area * pages) / float(2) * paper_weight / float(1000)

            # Calculated_Ink
            booklet.calculated_ink = booklet.calculated_mass * .04

            #Calculated_hours
            booklet.calculated_hours = booklet.job_id.planned_quantity / float(60)


class Edition(models.Model):
    _name = "wobe.edition"
    _description = 'WOBE Edition'

    job_id = fields.Many2one('wobe.job', required=True, ondelete='cascade', index=True, copy=False)
    name = fields.Char('Edition', help='Edition Name', required=True)

    plate_amount = fields.Integer('Plate Amount')
    net_quantity   = fields.Integer('Net Qty', help='Prints Net')

    gross_quantity = fields.Integer('Gross Qty', help='Prints Gross')
    waste_start = fields.Integer('Waste Start')
    waste_total = fields.Integer('Waste Total')

    production_start = fields.Char('Production Start', help='Info DateTime Start')
    production_stop = fields.Char('Production End', help='Info DateTime End')
