# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import paramiko
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class FileTransfer(models.Model):
    _name = 'file.transfer'
    _rec_name = 'url'

    url = fields.Char(string="Server IP", help='IP address of the Server / Host machine', copy=False)
    port = fields.Integer(string="Port", copy=False, default=22)
    login = fields.Char(string="Login", copy=False)
    password = fields.Char(string="Password", copy=False)

    server_path = fields.Char(string="Download Path", copy=False, help="Source/Download Directory")
    local_path = fields.Char(string="Destination Path", copy=False, help="Destination/Copy Directory")

    rsa_key = fields.Text(string="RSA Key", help="Provide only if required", copy=False)
    msg = fields.Char(string="Connection Message", copy=False)
    active = fields.Boolean(string='Active', default=True)

    note = fields.Text(string='Note', default="Note:"
                                              "\nIn the Destination path: Please maintain the 3 directory structure as follows:"
                                              "\n1. 'to_read'"
                                              "\n2. 'read'"
                                              "\n3. 'error'")


    @api.onchange('server_path', 'local_path', 'rsa_key')
    def onchange_details(self):

        if self.server_path and not self.server_path.endswith('/'):
            self.server_path = self.server_path + '/'

        if self.server_path and not self.server_path.startswith('/'):
            self.server_path = '/' + self.server_path

        if self.local_path and not self.local_path.endswith('/'):
            self.local_path = self.local_path + '/'

        if self.local_path and not self.local_path.startswith('/'):
            self.local_path = '/' + self.local_path

        if self.rsa_key and self.rsa_key.isspace():
            self.rsa_key = ''


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
        ssh = False
        try:
            ssh = paramiko.SSHClient()
            ssh.load_system_host_keys()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            pkey = None
            look_for_keys = False
            if self.rsa_key:
                pkey = self.rsa_key
                look_for_keys = True
            ssh.connect(self.url, port=self.port, username=self.login, password=self.password, pkey=pkey, look_for_keys=look_for_keys)
            msg = 'Successfully connected to server'
            connect = True
        except Exception, msg:
            msg = str(msg).lstrip('[Errno None]')
        self.write({'msg': msg})
        self._cr.commit()
        return [connect, msg, ssh]

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
                ssh  = response[2]
                sftp = ssh.open_sftp()
                # to get all files at server path
                server_files = []
                for i in sftp.listdir(connection.server_path):
                    if i.lower().endswith('.xml'):
                        filepath = connection.server_path + i
                        file_attr = sftp.stat(filepath)
                        lstatout = str(file_attr).split()[0]
                        #check with type file
                        if 'd' not in lstatout:
                            server_files.append(i)
                for sfile in server_files:
                    sftp.get(connection.server_path + sfile, connection.local_path+'to_read/' + sfile)# copy file from server to local destination
                    sftp.unlink(connection.server_path + sfile)#remove file from server when it's downloaded
                sftp.close()
                ssh.close()
        except Exception:
            _logger.exception("Failed processing file transfer")

        # Execute WobeJob Creation
        Job = self.env['wobe.job']
        ctx = self._context.copy()
        ctx.update({'local_path': connection.local_path})
        return Job.with_context(ctx).read_xml_file()



