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
    job_ref = fields.Char('Job #', help='WobeJob/KBAJob/InfoJob reference', index=True)

    run_date = fields.Datetime('Cron Time', help='Cron run date/time')

    part = fields.Selection([('xml1', 'Xml1'), ('xml3', 'Xml3'), ('xml4', 'Xml4')], 'File Part')

    state = fields.Selection([('new', 'New/ Unpaired'), ('pending', 'Partially Done'), ('done', 'Done')], string='Status',
                             default='new', copy=False, required=True)
    company_id = fields.Many2one('res.company', 'Company')
    edition_count = fields.Integer('Edition Count', help='Print Editions')

    xmlfile = fields.Binary('XML File', help='Imported XML File')
    filename = fields.Char()
    is_duplicate = fields.Boolean('Duplicate Record')
    duplicate_ref = fields.Many2one('file.registry','Duplicate Ref#', help="Note: XML1 could be always reference of XML4")
    file_create_date = fields.Float('File Create Date')

    generated_by = fields.Char(string="Generated By", copy=False, help='XML4 generated by')
    issue_date = fields.Date('Issue Date', help='XML4 Issue date', copy=False)
    info_issue = fields.Char('Info Issue', help='XML4 Info Issue', copy=False)

    @api.multi
    def merge_xml4(self):
        for registry in self:
            vals = {}
            Job = False

            if registry.duplicate_ref and registry.is_duplicate:
                Job = registry.duplicate_ref.job_id
            elif not registry.duplicate_ref and not registry.is_duplicate:
                # XML4 Job reference doesn't matches with any XML3 consider compare with XML1
                if not self.search([('part', '=', 'xml3'), ('job_ref', '=', registry.job_ref)]):
                    xml1Reg = self.search([('part', '=', 'xml1'), ('issue_date', '=', registry.issue_date),('info_issue', '=', registry.info_issue)], limit=1)
                    if xml1Reg:
                        vals['duplicate_ref'] = xml1Reg.id # non matching JOBID for XML4 add reference of XML1 registry
                        Job = xml1Reg.job_id
            if Job:
                Job.update_job_edition(registry)
            if vals:
                registry.write(vals)
            return True

    @api.model
    def create(self, vals):
        condition = False
        if vals.get('part') == 'xml1':
            condition = [('part', '=', 'xml1'), ('bduorder_ref', '=', vals['bduorder_ref']),('edition_count', '=', vals['edition_count'])]
        elif vals.get('part') == 'xml3':
            condition = [('part', '=', 'xml3'), ('bduorder_ref', '=', vals['bduorder_ref']),('job_ref', '=', vals['job_ref'])]
        elif vals.get('part') == 'xml4':
            condition = [('part', '=', 'xml4'), ('job_ref', '=', vals['job_ref'])]
        if condition:
            reg_obj = self.search(condition, limit=1,order='file_create_date')
            if reg_obj:
                vals['is_duplicate'] = True
                vals['duplicate_ref'] = reg_obj.id
        res = super(Registry, self).create(vals)
        if res.part == 'xml4':
            res.merge_xml4()
        return res


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
                    issue_date = root.find('Newspaper').find('IssueDate').text
                    NewspaperTitle = (root.find('Newspaper').find('NewspaperTitle').text).upper()
                    vals.update({
                        'part': 'xml1',
                        'bduorder_ref': BDUOrder,
                        'edition_count': edCnt,
                        'issue_date': issue_date,
                        'info_issue': NewspaperTitle, #XML1 NewspaperTitle to info_issue
                        })

                elif header.get('SenderId') == 'WOBEWorkflow' and header.get('Type') == 'PlatesUsed':
                    BDUOrder = root.find('Newspaper').find('BduOrderId').text
                    KBAJobId = root.find('Newspaper').find('WobeJobId').text.split(':')[2]
                    vals.update({
                        'part': 'xml3',
                        'bduorder_ref': BDUOrder,
                        'job_ref': KBAJobId,
                        })

                elif header.get('{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation') == 'kba_reportdata.xsd':
                    KBAJobId = root.find('info_jobid').text
                    info_issue = (root.find('info_issue').text).upper()
                    issue_date = root.find('info_issue_date').text
                    generated_by = ((root.find('generated_by').text).split(';')[0]).upper()
                    vals.update({
                        'part': 'xml4',
                        'job_ref': KBAJobId,
                        'generated_by':generated_by,
                        'info_issue':info_issue,
                        'issue_date':issue_date,
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
