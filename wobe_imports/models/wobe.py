# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
import logging
from datetime import datetime
import os
import base64
import xml.etree.ElementTree as ET
from collections import defaultdict
from product import PrintCategory


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

        prodStart = self.edition_ids and min(line.production_start for line in self.edition_ids) or False
        prodEnd = self.edition_ids and max(line.production_stop for line in self.edition_ids) or False

        self.production_start = prodStart
        self.production_stop = prodEnd

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
    edition_ids = fields.One2many('wobe.edition', 'job_id', 'Editions', copy=False)

    paper_product_ids = fields.One2many('wobe.paper.product', 'job_id', 'Paper Products', copy=False)

    state = fields.Selection([('waiting', 'Waiting'), ('ready', 'Ready'),
                             ('order_created', 'Order Created'),('picking_created', 'Picking Created'),
                             ('exception', 'Exception')], string='Status', default='waiting',
                             copy=False, required=True, track_visibility='onchange')

    order_id = fields.Many2one('sale.order', string='Sale Order', ondelete='restrict', help='Associated Sale Order')
    picking_id = fields.Many2one('stock.picking', string='Picking', ondelete='restrict', help='Associated Stock Picking')
    company_id = fields.Many2one('res.company', 'Company')
    file_count = fields.Integer('Files', compute='_compute_file_count')
    edition_count = fields.Integer('Edition Count')

    job_type = fields.Selection([('kba', 'KBA'), ('regioman', 'Regioman')],string='Type', default='kba',
                                track_visibility='onchange')
    stock_ok = fields.Boolean('Ok to create Stock?', default=False)
    convert_ok = fields.Boolean('Allow conversion of Job to Regioman?', default=True, copy=False)


    def _compute_file_count(self):
        file_registry = self.env['file.registry'].read_group([('job_id', 'in', self.ids)], ['job_id'], ['job_id'])
        res = dict((data['job_id'][0], data['job_id_count']) for data in file_registry)
        for line in self:
            line.file_count = res.get(line.id, 0)

    @api.model
    def _needaction_domain_get(self):
        return [('state', '=', 'exception')]


    @api.multi
    @api.constrains('edition_ids')
    def _check_editionRegioman(self):
        for case in self:
            if case.job_type == 'regioman' and len(case.edition_ids) > 1:
                    raise ValidationError(_('Regioman cannot have more than 1 Edition Details'))

    @api.multi
    def action_create_job(self):
        '''
            Extract data from XML-data stored in File-Registry
            & Create Job records
        '''
        Job_obj = self.env['wobe.job']
        Reg = self.env['file.registry']

        groupedFiles = defaultdict(lambda: {'Rfile1': False, 'Rfile3N4': {}, 'Rfile3':[]})
        part1, part3, part4 = {}, {}, {}

        # ----------------------------
        # Registry Files: Search
        # ----------------------------
        for x1 in Reg.search([('state','<>','done'), ('part','=', 'xml1')]
                , order='run_date, file_create_date, is_duplicate'):
            part1[x1.bduorder_ref] = [x1, x1.edition_count]

        for x3 in Reg.search([('state','<>','done'), ('part','=', 'xml3')]
                , order='run_date, file_create_date, is_duplicate'):
            BDUOrder = x3.bduorder_ref
            KBAJobId = x3.job_ref
            if not BDUOrder in part3:
                part3[BDUOrder] = {KBAJobId: x3}
            else:
                part3[BDUOrder].update({KBAJobId: x3})

        for x4 in Reg.search([('state','<>','done'), ('part','=', 'xml4')]
                , order='run_date, file_create_date, is_duplicate'):
            part4[x4.job_ref] = x4

        # ---------------------------------------
        # Files are linked & grouped: <Xml1>
        # ---------------------------------------
        for key in part1.keys():
            Rfile1 = part1[key][0]
            groupedFiles[key] = {'Rfile1': Rfile1, 'Rfile3N4': {}, 'Rfile3':[]}

        # ---------------------------------------------------------------
        # Files are linked & grouped: <Xml1> => <Xml3> => [<Xml4>]
        # ---------------------------------------------------------------
        for key in set(part1).intersection(set(part3)):

            map3N4, unmap3 = {}, []
            for y in set(part3[key]).intersection(set(part4)):
                f3, f4 = part3[key][y], part4[y]
                map3N4[f3] = f4

            for z in set(part3[key]) - set(part3[key]).intersection(set(part4)):
                regF3 = part3[key][z]
                if regF3.state == 'new':
                    unmap3.append(regF3)

            groupedFiles[key].update({'Rfile3N4': map3N4, 'Rfile3': unmap3})

        # --------------------------
        # Extract Data & Create job
        # --------------------------
        for key, fv in groupedFiles.iteritems():
            Reg1 = fv['Rfile1']

            File1 = base64.decodestring(Reg1.xmlfile)
            job = Job_obj.search([('bduorder_ref', '=', key)], limit=1)
            if job:
                # Pairing not allowed for Regioman Jobs
                if job.job_type == 'regioman':
                    continue

            try:
                tree1 = ET.fromstring(File1)
                data1 = tree1.find('Newspaper')

                edData = {}
                # Mapped files: <Xml3> && <Xml4>
                for Reg3, Reg4 in fv['Rfile3N4'].iteritems():
                    File3 = base64.decodestring(Reg3.xmlfile)
                    File4 = base64.decodestring(Reg4.xmlfile)

                    tree3 = ET.fromstring(File3)
                    data3 = tree3.find('Newspaper')

                    data4 = ET.fromstring(File4)

                    edData.update(self._extract_EditionData(edData, Reg3, data3, Reg4, data4))

                # UnMapped files: <Xml3>
                for Reg3 in fv['Rfile3']:
                    File3 = base64.decodestring(Reg3.xmlfile)
                    tree3 = ET.fromstring(File3)
                    data3 = tree3.find('Newspaper')

                    edData.update(self._extract_EditionData(edData, Reg3, data3))

                if not job:
                    vals = self._prepare_job_data(data1, edData)
                    vals['company_id'] = Reg1.company_id.id or self.env.user.company_id.id
                    job = Job_obj.create(vals)

                elif job.state in ('waiting', 'ready', 'exception'):
                    vals = self._prepare_job_data(data1, edData, Job=job)
                    job.write(vals)
                else:
                    continue

                # --------------------------------------------
                # Regitry: Update Status
                # --------------------------------------------
                rDone = {'job_id': job.id, 'state':'done'}
                rPending = {'job_id': job.id, 'state':'pending'}

                def _update_RegStatus(RgFile, Rvals):
                    RgFile.write(Rvals)
                    if RgFile.duplicate_ref:
                        _update_RegStatus(RgFile.duplicate_ref, Rvals)

                QtyCheck = job.net_quantity >= job.planned_quantity
                EditionCheck = len(job.edition_ids) == job.edition_count and all(l.net_quantity for l in job.edition_ids)

                if QtyCheck or EditionCheck:
                    _update_RegStatus(Reg1, rDone)
                else:
                    _update_RegStatus(Reg1, rPending)

                for rf in fv['Rfile3N4'].keys() + fv['Rfile3N4'].values():
                    _update_RegStatus(rf, rDone)

                for rf in fv['Rfile3']:
                    _update_RegStatus(rf, rPending)

            except:
                pass

        self._reset_Job_status()
        return True


    @api.multi
    def _prepare_job_data(self, data1, edData, Job=False):
        res = {}
        edlines, lines = [], []

        editionInfoL = ['plate_amount', 'net_quantity', 'gross_quantity', 'net_quantity',
                        'production_start', 'production_stop', 'waste_start', 'waste_total',
                        'kbajob_ref', 'infojob_ref', 'info_product']

        commonInfoL = ['plate_type',
                       'paper_mass_1', 'paper_mass_2', 'paper_mass_3', 'paper_mass_4', 'paper_mass_5',
                       'paper_mass_6', 'paper_mass_7',
                       'paper_width_1', 'paper_width_2', 'paper_width_3', 'paper_width_4', 'paper_width_5',
                       'paper_width_6', 'paper_width_7']

        # Edition Lines
        for key, val in edData.iteritems():
            name = key
            found = False

            if Job:
                found = Job.edition_ids.filtered(lambda x: x.name == key)
                if not found and key.isalpha():
                    found = Job.edition_ids.filtered(lambda x: x.name == val.get('infojob_ref'))

            elnvals = {'name' : name }
            for x in editionInfoL:
                elnvals[x] = val.get(x, False)

            # Note: paper/Other Info
            # remains same for all Editions
            for y in commonInfoL:
                res[y] = val.get(y)

            if found:
                edlines.append((1, found.id, elnvals))
            else:
                edlines.append((0,0, elnvals))

        # Booklet Lines
        for booklet in data1.iter('Booklet'):
            ref = booklet.get('id')
            found = False

            if Job:
                found = Job.booklet_ids.filtered(lambda x: x.booklet_ref == ref)

            weight = booklet.find('PaperWeight').text
            weight = 65 if float(weight) == 70 else weight

            lnvals = {
                'booklet_ref': ref,
                'pages' : booklet.find('Pages').text,
                'format': booklet.find('Format').text,
                'paper_weight': weight,

                'stitching': True if booklet.find('Stitching').text == 'Yes' else False,
                'glueing'  : True if booklet.find('Glueing').text == 'Yes' else False,
            }

            if found:
                lines.append((1, found.id, lnvals))
            else:
                lines.append((0,0, lnvals))


        res.update({
            'title'   : data1.find('NewspaperTitle').text,
            'edition_count': len(data1.findall('Edition')),

            'issue_date' : data1.find('IssueDate').text,
            'total_pages': int(data1.find('TotalPages').text or 0),
            'strook': data1.find('Strook').text,
            'planned_quantity': int(data1.find('ProductionAmount').text or 0),

            'edition_ids' : edlines,
            'booklet_ids' : lines,
               })

        if Job: return res
        # Data: for New-Job Record
        res.update({
            'job_ref' : data1.find('WobeJobId').text,
            'bduorder_ref': data1.find('BduOrderId').text,
            'name'    : data1.find('BduOrderId').text,
            })

        return res


    @api.multi
    def _extract_EditionData(self, res, RegFile3=False, data3={}, RegFile4=False, data4={}):
        '''
            Data extracted from XMLFile3 & XMLFile4
            Note:
                Key will be either be Edition-Name or WinpressJob-Id, depending on file (unpaired),
                But when both files are paired, then the key will be changed to
                reflect Edition-Name. (e.g. 'TZE')

        '''
        evals = {}

        if RegFile3:
            Plates = data3.find('PlatesUsed')
            evals.update({
                'kbajob_ref'  : RegFile3.job_ref,
                'plate_type'  : Plates.find('PlateType').text,
                'plate_amount': int(Plates.find('PlateAmount').text or 0),
                })

        if RegFile4:
            evals.update({
                'infojob_ref' : RegFile4.job_ref,
                'info_product': data4.find('info_product').text,

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
               })

        key = False
        if RegFile4:
            key = evals['info_product']

        elif RegFile3:
            key = RegFile3.job_ref

        if key not in res:
            res[key] = evals
        else:
            res[key].update(evals)

        return res


    @api.multi
    def action_create_order(self):
        sale_obj = self.env['sale.order']
        Registry = self.env['file.registry']

        Jobs = self.search([('state','=', 'ready'), ('order_id','=',False)])

        for case in Jobs:

            vals = case._prepare_order_data()
            if vals:
                order = sale_obj.create(vals)
                order_id = order.id # action confirm inherited and super returns false for job SO
                order.action_confirm()
                order = self.env['sale.order'].browse(order_id)
                order.message_post_with_view('mail.message_origin_link',
                    values={'self': order, 'origin': case},
                    subtype_id=self.env.ref('mail.mt_note').id)

                case.write({'state': 'order_created', 'order_id': order.id})
                Registry.search([('job_id','=', case.id), ('state', '<>', 'done')]).write({'state': 'done'})

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
            'job_id': self.id,
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
                search_format = [booklet.format]
                if booklet.format == 'MAG':
                    search_format = ['MAG', 'MP']
                dup_booklet_ids = (self.booklet_ids.filtered(lambda r: (r.format in search_format and r.paper_weight == booklet.paper_weight)))
                pages = 0
                for booklet_obj in dup_booklet_ids:
                    booklet_processed_ids.append(booklet_obj.id)
                    pages += int(booklet_obj.pages)
                ###################
                v1 = variant_obj.search([('name','=', str(pages)), ('attribute_id','=', pPages.id)])
                paper_weight = float(booklet.paper_weight)
                paper_weight = int(paper_weight) if paper_weight % 1 == 0 else paper_weight
                v2 = variant_obj.search([('name','=', str(paper_weight)), ('attribute_id','=', pWeight.id)])
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
            lines.append(_get_linevals(glueing, qty=1))

        # Stitching:
        if stitchCnt:
            if not stitching:
                self.message_post(body=_("Product not found for the print-category : 'Stitching'"))
                return {}
            lines.append(_get_linevals(stitching, qty=1))

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
    def _reset_Job_status(self):

        # Exceptions/Waiting:
        for job in self.search([('state','in', ('exception','waiting'))]):
            QtyCheck = job.net_quantity >= job.planned_quantity
            EditionCheck = len(job.edition_ids) == job.edition_count and all(l.net_quantity for l in job.edition_ids)

            if QtyCheck or EditionCheck:
                job.write({'state': 'ready'})

            elif job.state == 'exception':
                job.write({'state': 'waiting'})

            job._onchange_convert_flag()


    @api.multi
    def action_reset(self):
        self._reset_Job_status()

    @api.multi
    def action_force_ready(self):
        self.message_post(body=_("Force assign to 'Ready' status."))
        self.write({'state':'ready'})

    @api.multi
    def action_view_sales(self):
        self.ensure_one()
        action = self.env.ref('sale.action_orders')
        return {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'view_type': 'form' if self.order_id else action.view_type,
            'view_mode': 'form' if self.order_id else action.view_mode,
            'target': action.target,
            'res_id': self.order_id.id or False,
            'res_model': action.res_model,
            'domain': [('id', '=', self.order_id.id)],
        }

    @api.multi
    def action_view_picking(self):
        self.ensure_one()
        action = self.env.ref('stock.action_picking_tree_all')
        return {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'view_type': 'form' if self.picking_id else action.view_type,
            'view_mode': 'form' if self.picking_id else action.view_mode,
            'target': action.target,
            'res_id': self.picking_id.id or False,
            'res_model': action.res_model,
            'domain': [('id', '=', self.picking_id.id)],
        }

    @api.multi
    def action_view_file_registry(self):
        self.ensure_one()
        action = self.env.ref('wobe_imports.action_file_registry').read()[0]
        file_registry = self.env['file.registry'].search([('job_id', 'in', self._ids)])
        if len(file_registry) > 1:
            action['domain'] = [('id', 'in', file_registry.ids)]
        elif file_registry:
            action['views'] = [(self.env.ref('wobe_imports.view_file_registry_form').id, 'form')]
            action['res_id'] = file_registry.id
        else:
            action['domain'] = [('id', 'in', file_registry.ids)]
        action['context'] = {}
        return action

    @api.model
    def create(self, vals):
        res = super(Job, self).create(vals)
        res._fetch_paperProducts()
        return res

    @api.multi
    def _fetch_paperProducts(self):
        self.ensure_one()
        lines = []
        product_obj = self.env['product.product']
        prodTemp_obj = self.env['product.template']
        variant_obj = self.env['product.attribute.value']

        domain = [('print_category','=', 'paper_regioman')]

        MassX, WidthX = set(), set()
        for idx in range(1, 8):
            m = self['paper_mass_' + str(idx)]
            if m: MassX.add(m)

            w = self['paper_width_' + str(idx)]
            if w: WidthX.add(w)

        pMass  = self.env.ref('wobe_imports.variant_attribute_3', False)
        pWidth = self.env.ref('wobe_imports.variant_attribute_paperWidth', False)
        msg, stockOk = '', True

        # Products: Paper Regioman
        if not MassX or self.job_type == 'regioman':
            prods = product_obj.search(domain)
            for p in prods:
                lines.append({'product_id': p.id,})

            if not prods:
                self.message_post(body=_("Product not found for the print-category : 'Paper Regioman'"))
                stockOk = False

        # Products: Paper KBA
        for M in MassX:
            for W in WidthX:
                m1 = M / 100.0
                m1 = int(m1) if m1%1 == 0 else m1

                v1 = variant_obj.search([('name','=', str(m1)), ('attribute_id','=', pMass.id)])
                v2 = variant_obj.search([('name','=', str(W)), ('attribute_id','=', pWidth.id)])
                product = product_obj.search([('attribute_value_ids', 'in', v1.ids),
                                              ('attribute_value_ids', 'in', v2.ids),
                                              ('print_category','=', 'paper_kba')]
                                             , order='id desc', limit=1)

                if not product:
                    msg += '(%s, %s); '%(m1, W)
                    continue
                lines.append({'product_id': product.id,})

        if msg:
            self.message_post(body=_("Product not found for the print-category : 'Paper KBA' for these variants - %s"%msg))
            stockOk = False

        lines = map(lambda x: (0,0, x), lines)
        self.write({'paper_product_ids': lines, 'stock_ok': stockOk})
        return True

    @api.one
    def button_convert_regioman(self):
        "Mark Job as 'Regioman' "

        self.write({
            'job_type': 'regioman', 'convert_ok': False,
            'edition_ids': map(lambda x: (2, x), [x.id for x in self.edition_ids])
            })

    @api.onchange('state', 'job_type')
    def _onchange_convert_flag(self):
        if self.state == 'waiting' and self.job_type == 'kba':
            self.convert_ok = True

        else: self.convert_ok = False


    @api.model
    def _prepare_picking(self):
        picking_type = self.env['stock.picking.type'].search([('code','=','outgoing'),('warehouse_id.company_id','=',self.company_id.id)])
        aa = self.env['account.analytic.account'].search([('name', '=', self.title)])
        partner = aa and aa.partner_id or False

        return  {
            'picking_type_id': picking_type.id,
            'partner_id': partner.id,
            'min_date': self.issue_date+' '+datetime.now().strftime("%H:%M:%S"),
            'origin': self.name,
            'location_dest_id': partner.property_stock_customer.id,
            'location_id': picking_type.default_location_src_id.id,
            'company_id': self.company_id.id,
        }

    def _prepare_stock_moves(self, job, line,  picking):
        """ Prepare the stock moves data from line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        res = []
        product_obj = line['productObj']
        if product_obj.type not in ['product', 'consu']:
            return res
        template = {
            'name': line['name'] or '',
            'product_id': product_obj.id,
            'product_uom': product_obj.uom_id.id,
            'product_uom_qty': line['product_uom_qty'],
            'date': job.issue_date,
            'date_expected': picking.min_date,
            'location_id':picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
            'picking_id': picking.id,
            'partner_id': picking.partner_id.id,
            'move_dest_id': False,
            'state': 'draft',
            'company_id': picking.company_id.id,
            'picking_type_id': picking.picking_type_id.id,
            'group_id': picking.group_id.id,
            'procurement_id': False,
            'origin': picking.origin,
            'route_ids': picking.picking_type_id.warehouse_id and [
                (6, 0, [x.id for x in picking.picking_type_id.warehouse_id.route_ids])] or [],
            'warehouse_id': picking.picking_type_id.warehouse_id.id,
        }
        res.append(template)
        return res

    def _prepare_picking_lines(self, job, picking):
        product_obj = self.env['product.product']
        lines = []
        print_category3, print_category4, name3, name4 = '', '', '', ''
        qty3, qty4 = job.plate_amount, int(sum(bookObj.calculated_ink for bookObj in job.booklet_ids))

        for paper_line in job.paper_product_ids:
            # total_mass_per_paper_type = sum(bookObj.calculated_mass for bookObj in job.booklet_ids) * job.net_quantity
            # total_paper_width = sum(job.paper_width_1+job.paper_width_2+job.paper_width_3+job.paper_width_4+job.paper_width_5+job.paper_width_6)
            lines.append({'productObj': paper_line.product_id, 'name': paper_line.name, 'product_uom_qty': 1})

        if job.plate_type == 'PA':
            print_category3 = 'plates_kba'
            print_category4 = 'ink_kba'
            name3 = 'Plates'
        else:
            print_category3 = 'plates_regioman'
            print_category4 = 'ink_regioman'
            name3 = 'Ink'

        product3 = product_obj.search([('print_category', '=', print_category3)])
        product4 = product_obj.search([('print_category', '=', print_category4)])
        if not product3:
            body = _("Product not found for the print-category : '%s'" % (dict(PrintCategory)[print_category3]))
            picking.message_post(body=body)
            return {}
        if not product4:
            body = _("Product not found for the print-category : '%s'" % (dict(PrintCategory)[print_category4]))
            picking.message_post(body=body)
            return []
        lines.append({'productObj': product3, 'name': name3, 'product_uom_qty': qty3})
        lines.append({'productObj': product4, 'name': name4, 'product_uom_qty': qty4})
        return lines

    def _create_stock_moves(self, job, picking):
        moves = self.env['stock.move']
        done = self.env['stock.move'].browse()
        lines = self._prepare_picking_lines(job, picking)
        for line in lines:
            for val in self._prepare_stock_moves(job, line, picking):
                done += moves.create(val)
        return done

    @api.multi
    def action_create_picking(self):
        StockPicking = self.env['stock.picking']
        Jobs = self.search([('state','=','order_created'),('picking_id','=',False),('stock_ok','=',True)])
        for case in Jobs:
            res = case._prepare_picking()
            picking = StockPicking.create(res)
            self._create_stock_moves(case, picking)
            picking.message_post_with_view('mail.message_origin_link',
                                           values={'self': picking, 'origin': case},
                                           subtype_id=self.env.ref('mail.mt_note').id)
            if not picking.group_id:
                picking.group_id = picking.group_id.create({
                    'name': case.name,
                    'partner_id': picking.partner_id.id
                })
            case.write({'picking_id':picking.id,'state':'picking_created'})
        return True

    @api.model
    def create(self, vals):
        res = super(Job, self).create(vals)
        res._fetch_paperProducts()
        return res

    @api.multi
    def _fetch_paperProducts(self):
        self.ensure_one()
        lines = []
        product_obj = self.env['product.product']
        prodTemp_obj = self.env['product.template']
        variant_obj = self.env['product.attribute.value']

        domain = [('print_category','=', 'paper_regioman')]

        MassX, WidthX = set(), set()
        for idx in range(1, 8):
            m = self['paper_mass_' + str(idx)]
            if m: MassX.add(m)

            w = self['paper_width_' + str(idx)]
            if w: WidthX.add(w)

        pMass  = self.env.ref('wobe_imports.variant_attribute_3', False)
        pWidth = self.env.ref('wobe_imports.variant_attribute_paperWidth', False)
        msg, stockOk = '', True

        # Products: Paper Regioman
        if not MassX or self.job_type == 'regioman':
            prods = product_obj.search(domain)
            for p in prods:
                lines.append({'product_id': p.id,})

            if not prods:
                self.message_post(body=_("Product not found for the print-category : 'Paper Regioman'"))
                stockOk = False

        # Products: Paper KBA
        for M in MassX:
            for W in WidthX:
                m1 = M / 100.0
                m1 = int(m1) if m1%1 == 0 else m1

                v1 = variant_obj.search([('name','=', str(m1)), ('attribute_id','=', pMass.id)])
                v2 = variant_obj.search([('name','=', str(W)), ('attribute_id','=', pWidth.id)])
                product = product_obj.search([('attribute_value_ids', 'in', v1.ids),
                                              ('attribute_value_ids', 'in', v2.ids),
                                              ('print_category','=', 'paper_kba')]
                                             , order='id desc', limit=1)
                if not product:
                    msg += '(%s, %s); '%(m1, W)
                    continue
                lines.append({'product_id': product.id,})

        if msg:
            self.message_post(body=_("Product not found for the print-category : 'Paper KBA' for these variants - %s"%msg))
            stockOk = False

        lines = map(lambda x: (0,0, x), lines)
        self.write({'paper_product_ids': lines, 'stock_ok': stockOk})
        return True



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
            plates = 0.0
            pages = float(booklet.pages)
            paper_weight = float(booklet.paper_weight)
            format = 'MP' if booklet.format == 'MAG' else booklet.format
            if pages <= 48.0:
                plates = pages * 4
            elif pages > 48.0:
                if format == 'BS':
                    plates = pages * 4
                elif format == 'TB':
                    plates = pages * 2
                elif format == 'MP':
                    plates = pages
            booklet.calculated_plates = plates

            #calculated_mass
            booklet.calculated_mass = 0.0
            product_obj = self.env['product.product']
            variant_obj = self.env['product.attribute.value']
            pPages = self.env.ref('wobe_imports.variant_attribute_2', False)
            pWeight = self.env.ref('wobe_imports.variant_attribute_3', False)

            paper_weight = int(paper_weight) if paper_weight % 1 == 0 else paper_weight
            v1 = variant_obj.search([('name', '=', booklet.pages), ('attribute_id', '=', pPages.id)])
            v2 = variant_obj.search([('name', '=', str(paper_weight)), ('attribute_id', '=', pWeight.id)])

            product = product_obj.search([('attribute_value_ids', 'in', v1.ids),
                                          ('attribute_value_ids', 'in', v2.ids),
                                          ('print_format_template', '=', True),
                                          ('formats', '=', format), ], order='id desc', limit=1)
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
    name = fields.Char('Edition', help='Edition Name', required=True, copy=False)

    plate_amount = fields.Integer('Plate Amount')
    net_quantity = fields.Integer('Net Qty', help='Prints Net')

    gross_quantity = fields.Integer('Gross Qty', help='Prints Gross')
    waste_start = fields.Integer('Waste Start')
    waste_total = fields.Integer('Waste Total')

    production_start = fields.Datetime('Production Start', help='Info DateTime Start')
    production_stop = fields.Datetime('Production End', help='Info DateTime End')

    kbajob_ref  = fields.Char('KBA Job #', help='KBA Job (XML3)', copy=False)
    infojob_ref = fields.Char('Info Job #', help='Info Job (XML4)', copy=False)
    info_product = fields.Char('Info Product', help='Info product / Edition Name', copy=False)

    @api.onchange('name')
    def edition_create(self):
        self.name = self.job_id.title
        self.plate_amount = sum(line.calculated_plates if int(line.pages) >= 48 else line.calculated_plates / 2 for line in self.job_id.booklet_ids)
        self.net_quantity = self.job_id.planned_quantity

    @api.onchange('gross_quantity')
    def waste_compute(self):
        self.waste_total = 0
        if self.gross_quantity > self.net_quantity:
            self.waste_total = self.gross_quantity - self.net_quantity


class Registry1(models.Model):
    _inherit = "file.registry"

    job_id = fields.Many2one('wobe.job', ondelete='set null', index=True, copy=False)

    @api.multi
    def action_view_job(self):
        self.ensure_one()
        action = self.env.ref('wobe_imports.action_wobe_job')
        return {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'view_type': 'form' if self.job_id else action.view_type,
            'view_mode': 'form' if self.job_id else action.view_mode,
            'target': action.target,
            'res_id': self.job_id.id or False,
            'res_model': action.res_model,
            'domain': [('id', '=', self.job_id.id)],
        }


class PaperProduct(models.Model):
    _name = "wobe.paper.product"
    _description = 'WOBE Paper Product'

    job_id = fields.Many2one('wobe.job', required=True, ondelete='cascade', index=True, copy=False)
    product_id = fields.Many2one('product.product', 'Product', required=True)
    name = fields.Char(related='product_id.default_code', string='Internal Reference', store=True)

