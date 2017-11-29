# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import ftputil
import ftputil.session
from odoo.exceptions import UserError
import logging
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

    note = fields.Text(string='Note', default="Note:"
                                              "\nIn the Destination path: Please maintain the 3 directory structure as follows:"
                                              "\n1. 'To_read'"
                                              "\n2. 'Read'"
                                              "\n3. 'Error'")


    @api.onchange('server_path', 'local_path')
    def onchange_details(self):

        if self.server_path and not self.server_path.endswith('/'):
            self.server_path = self.server_path + '/'

        if self.server_path and not self.server_path.startswith('/'):
            self.server_path = '/' + self.server_path

        if self.local_path and not self.local_path.endswith('/'):
            self.local_path = self.local_path + '/'

        if self.local_path and not self.local_path.startswith('/'):
            self.local_path = '/' + self.local_path

    @api.model
    def create(self, vals):
        if len(self.search([('active','=',True)])) >= 1 and vals['active'] == True :
            raise UserError(_("You can't create more than one active connection"))

        return super(FileTransfer, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.has_key('active') and vals.get('active'):
            if self.search([('id','not in', self._ids),('active', '=', True)]):
                raise UserError(_("You can't create more than one active connection"))

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

    @api.model
    def process_file_transfer(self, ids=None):
        connection = self.search([('active','=',True)])
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
                    dest_path = str(connection.local_path+'To_read/'+ sfile)
                    source = ftp.open(src_path, 'r')  # file-like object
                    target = ftp.open(dest_path, 'w')  # file-like object
                    ftp.copyfileobj(source, target)
                    # ftp.download(src_path, dest_path)# download files from server
                    source.close()
                    target.close()
                    ftp.remove(src_path)  # remove server file
                ftp.close()
        except Exception:
            _logger.exception("Failed processing file transfer")
        # Execute WobeJob Creation
        Job = self.env['wobe.job']
        ctx = self._context.copy()
        ctx.update({'local_path': connection.local_path})
        return Job.with_context(ctx).read_xml_file()



