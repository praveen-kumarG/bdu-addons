# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import ftputil
import ftputil.session
from odoo.exceptions import UserError
import logging

import os
import base64
import xml.etree.ElementTree as ET

_logger = logging.getLogger(__name__)


class FileTransfer(models.Model):
    _name = 'file.transfer'
    _rec_name = 'url'

    url = fields.Char(string="Server IP", help='IP address of the Server / Host machine', copy=False)
    port = fields.Integer(string="Port", copy=False, default=21)
    login = fields.Char(string="Login", copy=False)
    password = fields.Char(string="Password", copy=False)

    server_path = fields.Char(string="Download Path", copy=False, help="Source/Download Directory")
    local_path = fields.Char(string="Destination Path", copy=False, help="Destination/Copy Directory")

    msg = fields.Char(string="Connection Message", copy=False)
    active = fields.Boolean(string='Active', default=True)

    company_id = fields.Many2one('res.company', 'Company', help='Company, to which records needs to be imported',
                                 default=lambda self: self.env['res.company']._company_default_get('sale.order'))



    # @api.onchange('server_path', 'local_path')
    # def onchange_details(self):
    #     if self.server_path and not self.server_path.endswith('/'):
    #         self.server_path = self.server_path + '/'
    #
    #     if self.server_path and not self.server_path.startswith('/'):
    #         self.server_path = '/' + self.server_path
    #
    #     if self.local_path and not self.local_path.endswith('/'):
    #         self.local_path = self.local_path + '/'
    #
    #     if self.local_path and not self.local_path.startswith('/'):
    #         self.local_path = '/' + self.local_path


    @api.model
    def create(self, vals):
        if len(self.search([('active','=',True),('company_id','=',vals.get('company_id'))])) >= 1 and vals['active'] == True :
            raise UserError(_("You can't create more than one active connection same company"))

        return super(FileTransfer, self).create(vals)

    @api.multi
    def write(self, vals):
        assert len(self.ids) == 1, "you can open only one session at a time"
        active = False
        if vals.has_key('active') or vals.has_key('company_id'):
            if vals.has_key('active'):
                active = vals.get('active')
            else:
                active = self.active
            if active:
                if vals.has_key('company_id') and vals.get('company_id'):
                    company_id = vals.get('company_id')
                else:
                    company_id = self.company_id.id
                if self.search([('id','not in',self._ids),('active', '=', True),('company_id', '=', company_id)]):
                    raise UserError(_("You can't create more than one active connection for same company"))

        return super(FileTransfer, self).write(vals)


    @api.multi
    def test_connection(self):
        msg = ''
        connect = False
        ftp = False
        try:
            port_session_factory = ftputil.session.session_factory(port=self.port)
            ftp = ftputil.FTPHost(self.url, self.login, self.password, session_factory = port_session_factory)
            msg = 'Successfully connected to server'
            connect = True
        except Exception, msg:
            msg
        self.write({'msg': msg})
        self._cr.commit()
        return [connect, msg, ftp]

    @api.multi
    def check_connection(self):
        msg = self.test_connection()
        raise UserError(msg[1])

    @api.multi
    def process_file_transfer(self):
        connection = self.search([('active','=',True),('company_id','=',self.env.user.company_id.id)])
        if not connection:
            _logger.exception("FTP Connection does not exist, please configure under 'FTP Settings'.")
            return False

        # Initiate File Transfer
        try:
            response = connection.test_connection()
            if response[0]:
                ftp  = response[2]
                # to get all files at server path
                server_files = []
                for i in ftp.listdir(connection.server_path):
                    if ftp.path.isfile(connection.server_path+i) and i.lower().endswith('.xml'):
                        server_files.append(i)
                for sfile in server_files:
                    src_path  = str(connection.server_path + sfile)
                    dest_path = str(connection.local_path + sfile)
                    ftp.download(src_path, dest_path)# download files from server
                    ftp.remove(src_path)  # remove server file
                ftp.close()
        except Exception:
            _logger.exception("Failed processing file transfer")

        # Registry Creation
        Reg = self.env['file.registry']
        ctx = self._context.copy()
        ctx.update({'local_path': connection.local_path, 'company_id': connection.company_id.id})
        return Reg.with_context(ctx).load_xml_file()


    @api.model
    def run_wobejob_process(self, ids=None):
#        Job = self.env['wobe.job']

        # Call: FTP & Registry Creation
        self.process_file_transfer()
#        self._cr.commit()

        # Call: WobeJob Creation
#        Job.action_create_job()

        # Call: Sale Order Creation
#        Job.action_create_order()

        # Call: Picking Creation
#        Job.action_create_picking()

        # Call: Costing Creation
#        Job.action_create_costing()




class Registry(models.Model):
    _name = 'file.registry'
    _description = 'XML File Registry'
    _order = 'run_date desc, file_create_date desc'

    name = fields.Char('File Name', required=True, index=True)
    bduorder_ref = fields.Char('BDUOrder #', help='BDUOrder reference', index=True)

    run_date = fields.Datetime('Cron Time', help='Cron run date/time')

    part = fields.Selection([('xml1', 'Xml1'), ('xml3', 'Xml3'), ('xml4', 'Xml4'), ('xml1a', 'Xml1A'),('xml1b', 'Xml1B')], 'File Part')

    state = fields.Selection([('new', 'New/ Unpaired'), ('pending', 'Partially Done'), ('done', 'Done')], string='Status',
                             default='new', copy=False, required=True)
    company_id = fields.Many2one('res.company', 'Company')
    edition_count = fields.Integer('Edition Count', help='Print Editions')

    xmlfile = fields.Binary('XML File', help='Imported XML File')
    filename = fields.Char()
    file_create_date = fields.Float('File Create Date')

    generated_by = fields.Char(string="Generated By", copy=False, help='XML4 generated by')
    edition_name = fields.Char('Edition Name', help='XML1a & XML1b Short Label', copy=False)


    @api.multi
    def load_xml_file(self):
        '''
            Imports the XML file into FileRegistry
        '''

        path = self._context.get('local_path', '')
        companyID = self._context.get('company_id', '')
        dir_toRead = os.path.join(path)

        try:
            os.listdir(dir_toRead)
        except Exception, e:
            _logger.exception("Wobe Import File : %s" % str(e))
            return True
        # sort local path files based on creation date
        os.chdir(dir_toRead)
        fileLists = filter(os.path.isfile, os.listdir(dir_toRead))
        fileLists.sort(key=lambda x: os.path.getctime(x))

        if not fileLists:
            fileLists = os.listdir(dir_toRead)

        for filename in fileLists:
            if not filename.lower().endswith('.xml'): continue
            File = os.path.join(dir_toRead, filename)
            fileStat = os.stat(File)
            file_create_date = fileStat.st_ctime
            vals = {}

            try:
                tree = ET.parse(File)
                root = tree.getroot()
                header = root.attrib

                if header.get('SenderId') == 'WOBEWebportal' and header.get('Type') == 'CreateJob':
                    BDUOrder = root.find('Newspaper').find('BduOrderId').text
                    edCnt = len(root.find('Newspaper').findall('Edition'))
                    vals.update({
                        'part': 'xml1',
                        'bduorder_ref': BDUOrder,
                        'edition_count': edCnt,
                        })

                elif header.get('SenderId') == 'WOBEWorkflow' and header.get('Type') == 'PlatesUsed':
                    BDUOrder = root.find('Newspaper').find('BduOrderId').text
                    vals.update({
                        'part': 'xml3',
                        'bduorder_ref': BDUOrder,
                        })

                elif header.get('{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation') == 'kba_reportdata.xsd':
                    BDUOrder = root.find('info_BduOrderId').text
                    generated_by = ((root.find('generated_by').text).split(';')[0]).upper()
                    vals.update({
                        'part': 'xml4',
                        'bduorder_ref': BDUOrder,
                        'generated_by':generated_by,
                        })

                elif header.get('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation') == 'http://www.prime-network.com/ipopri/PlateProductionDefinition/R1.1.0 PRIME_NETWORK_PlateProductionDefinition_R1.1.0.xsd':
                    if "xml1a" in filename:
                        xml1aDt = self.parse_xml1a(root)
                        vals.update({
                            'part': 'xml1a',
                            'bduorder_ref':xml1aDt['BduOrderId'],
                            'edition_name': xml1aDt['EdName']
                        })
                    elif "xml1b" in filename:
                        xml1bDt = self.parse_xml1b(root)
                        vals.update({
                            'part': 'xml1b',
                            'bduorder_ref': xml1bDt['BduOrderId'],
                            'edition_name':xml1bDt['EdName']
                        })
                vals.update({
                    'name': filename,
                    'company_id': companyID,
                    'run_date': fields.Datetime.now(),
                })
                fn = open(File, 'r')
                vals.update({'filename': filename,
                             'xmlfile': base64.encodestring(fn.read()),'file_create_date':file_create_date,})
                fn.close()
                os.remove(File)#remove file from local system
                reg = self.create(vals)

            except Exception, e:
                _logger.exception("Wobe Import: File-Registry : %s" % str(e))

        return True


    def parse_xml1a(self, root):
        '''
            Parse the XML1a according to element namespace
        '''
        data = {}

        BduOrderEle = '{http://www.KBA.com/KNS/PrintProductDefinition/R2.1.0/ExJobData/R1.0.0}BduOrderId'
        BodyEle = "{http://www.ifra.com/IfraTrack/imf/4.1}Body"
        objEle = "{http://www.ifra.com/IfraTrack/isd/4.1}Object"
        labelEle = "{http://www.ifra.com/IfraTrack/ipo/4.1}ShortLabel"
        plannedCopiesEle = "{http://www.ifra.com/IfraTrack/ipo/4.1}PlannedCopies"

        for objs in root.find(BodyEle).findall(objEle):
            if objs.attrib['{http://www.w3.org/2001/XMLSchema-instance}type'] == "ipopri:Product":
                data['BduOrderId'] = objs.find(BduOrderEle).text
                data['EdName'] = objs.find(labelEle).text
                data['PlannedCopies'] = objs.find(plannedCopiesEle).text
                break
        return data

    def parse_xml1b(self, root):
        '''
            Parse the XML1b according to element namespace
        '''
        data, data['booklets'] = {}, {}

        Body = "{http://www.ifra.com/IfraTrack/imf/4.1}Body"
        labelEle = "{http://www.ifra.com/IfraTrack/ipo/4.1}ShortLabel"
        ipoEle = "{http://www.ifra.com/IfraTrack/ipo/4.1}"
        isdEle = "{http://www.ifra.com/IfraTrack/isd/4.1}"
        obj = isdEle + "Object"

        for objs in root.find(Body).findall(obj):
            if objs.attrib['{http://www.w3.org/2001/XMLSchema-instance}type'] == "ipo:Issue":
                data['BduOrderId'] = objs.find('.//iBduOrderId').text
            elif objs.attrib['{http://www.w3.org/2001/XMLSchema-instance}type'] == "ipopri:Product":
                data['EdName'] = objs.find(labelEle).text
            elif objs.attrib['{http://www.w3.org/2001/XMLSchema-instance}type'] == "ipo:Book":
                book = {}
                book['pages'] = objs.find(ipoEle + 'NoOfPage').text
                pageFormat = objs.find(ipoEle + 'PageFormat').text.lower()
                if pageFormat == 'tabloid':
                    pageFormat = 'TB'
                elif pageFormat == 'halftabloid':
                    pageFormat = 'MP'
                elif pageFormat == 'broadsheet':
                    pageFormat = 'BS'
                book['format'] = pageFormat
                book['paper_weight'] = objs.find('.//iPaperWeight').text
                BookPos = objs.find(ipoEle + 'BookPos').text
                objuid = objs.find(isdEle + 'ObjectUID').text
                book['booklet_ref'] = objuid.split(':')[2] if objuid else objuid
                data['booklets'][BookPos] = {}
                data['booklets'][BookPos] = book
        return data

