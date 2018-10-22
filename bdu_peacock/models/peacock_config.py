# -*- coding: utf-8 -*-

import datetime, ftputil,  ftputil.session, httplib, json, logging, pdb, requests, urllib
from lxml import etree 
from tempfile import TemporaryFile
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger(__name__)

class PeacockConfig(models.Model):
    _name          = 'peacock.config'
    _description   = 'Connection info for Schuiteman / Peacock Insights interface'
    server  	   = fields.Char(string='Server',         help="Servername, including protocol, e.g. https://prod.barneveldsekrant.nl" )
    directory	   = fields.Char(string='Server subdir',  help="Directory starting with slash, e.g. /api/v1, or empty")
    tempdir        = fields.Char(string='Local temp dir', help="Local temporary directory. e.g. /home/odoo")
    user           = fields.Char(string='User')
    password       = fields.Char(string='Password')
    days           = fields.Integer(string='History in days')

    latest_run     = fields.Char(string='Latest run',     help="Date of latest run of Announcement connector")
    latest_status  = fields.Char(string='Latest status',  help="Log of latest run")
    
    end		       = fields.Date(string='End', help="End date of date range in format yyyy-mm-dd")
    
    #show only first record to configure, no options to create an additional one
    @api.multi
    def default_view(self):
        configurations = self.search([])
        if not configurations :
            server = "bdu.nl"
            self.write({'server' : server})
            configuration = self.id
            _logger.info("configuration created")
        else :
            configuration = configurations[0].id
        action = {
                    "type":"ir.actions.act_window",
                    "res_model":"peacock.config",
                    "view_type":"form",
                    "view_mode":"form",
                    "res_id":configuration,
                    "target":"inline",
        }
        return action

    @api.multi
    def save_config(self):
        self.write({})
        return True

    def log_exception(self, msg, final_msg):
        config = self[0] 
        _logger.exception(final_msg)
        config.latest_run     = datetime.datetime.utcnow().strftime('UTC %Y-%m-%d %H:%M:%S ')
        config.latest_status  = msg+final_msg
        config.write({})
        return 

    def ship_file(self, dict, filename, conn):
        config = self[0]
        f = open(config.tempdir+"/"+filename,"w")
        data = json.dumps(dict)
        f.write(data)
        f.close

        #pdb.set_trace()
        try:
            _logger.info("Transfering " + filename)
            if config.directory :
                target = str(config.directory) + '/' + filename
            else :
                target = '/' + filename
            source = config.tempdir + '/' + filename
            conn.upload(source, target)
        except Exception, e:
            self.log_exception(msg,"Transfer failed, quiting....")
            return False


        return 


    @api.multi
    def automated_run(self):
        configurations = self.search([])
        if not configurations :
            #cannot use local method because there is no record
            _logger.exception(msg, "Cannot start automated_run. Need a valid configuration")
            return False
        else :
            #start with previous end
            self = configurations[0]
            self.end = datetime.date.today()
            self.write({})
            return self.do_send()

    
    @api.multi 
    def do_send(self):	
        msg    = ""    
        config = self[0] 
        if not config:
            self.log_exception(msg, "No configuration found. <br>Please configure Schuiteman Peacock connector.")
            return False
       
        if not config.end :
            self.log_exception(msg, "Program not started. <br>Please provide a valid date")
            return False

        if not config.days :
            self.log_exception(msg,"Program not started. <br>Please provide a valid period (i.e. history in days)")
            return False

        if not config.server or not config.user or not config.password or not config.tempdir:
            self.log_exception(msg,"Program not started. <br>Please provide a valid server/user/password/tempdir configuration")
            return False
        
        #calc begin and end date
        end   = datetime.datetime.strptime(config.end,DEFAULT_SERVER_DATE_FORMAT).date()
        begin = end - datetime.timedelta(days = config.days)
        end   = end.strftime(  'UTC %Y-%m-%d T23:59:59')
        begin = begin.strftime('UTC %Y-%m-%d T00:00:00')

        #account.move
        am =self.env['account.move'].search_read([      ('write_date', '>=', begin), \
                                                        ('write_date', '<=', end  )  \
                                                     ],['id',                        \
                                                        'name',                      \
                                                        'create_date',               \
                                                        'create_uid',                \
                                                        'write_date',                \
                                                        'write_uid',                 \
                                                        'operating_unit_id',         \
                                                        'company_id',                \
                                                        'journal_id',                \
                                                        'line_ids',                  \
                                                     ])
        
        #account.move.line
        aml =self.env['account.move.line'].search_read([ ('write_date', '>=', begin),\
                                                         ('write_date', '<=', end  ) \
                                                     ],['id',                        \
                                                        'name',                      \
                                                        'create_date',               \
                                                        'create_uid',                \
                                                        'write_date',                \
                                                        'write_uid',                 \
                                                        'operating_unit_id',         \
                                                        'company_id',                \
                                                        'account_id',                \
                                                        'analytic_account_id',       \
                                                        'analytic_line_ids',         \
                                                        'invoice_id',                \
                                                        'quantity',                  \
                                                        'product_id',                \
                                                        'partner_id',                \
                                                        'partner_bank_id',           \
                                                        'ref',                       \
                                                        'reconciled',                \
                                                        'tax_ids',                   \
                                                        'statement_id',              \
                                                        'narration',                 \
                                                        'bank_payment_line_id',      \
                                                        'full_reconcile_id',         \
                                                        #'l10n_nl_date_invoice',      \
                                                        'debit',                     \
                                                        'credit',                    \
                                                        'move_id',                   \
                                                     ])
        
        #account.account
        aa =self.env['account.account'].search_read([ ('deprecated','=',False   )    \
                                                     ],['id',                        \
                                                        'name',                      \
                                                        'create_date',               \
                                                        'create_uid',                \
                                                        'write_date',                \
                                                        'write_uid',                 \
                                                        'company_id',                \
                                                        'display_name',              \
                                                        'tag_ids',                   \
                                                        'code',                      \
                                                     ])

        #process into xml file 
        root         = etree.Element('report')
        chapter_am   = etree.Element('account_move')
        chapter_aml  = etree.Element('account_move_line')
        chapter_aa   = etree.Element('account_account')
        root.append(chapter_am)
        root.append(chapter_aml)
        root.append(chapter_aa)

        #files as chapters in one xml document
        for am_record in am :
            self.add_element(chapter_am, am_record, 'record')
        for aml_record in aml :
            self.add_element(chapter_aml, aml_record, 'record')
        for aa_record in aa :
            self.add_element(chapter_aa, aa_record, 'record')
        xml = etree.tostring(root, pretty_print=False) #pretty_print=True makes it readable but introduces a.o. \n chars

        # Initiate File Transfer Connection
        try:
            port_session_factory = ftputil.session.session_factory(port=21, use_passive_mode=True)
            ftp = ftputil.FTPHost(config.server, config.user, config.password, session_factory = port_session_factory)
        except Exception, e:
            self.log_exception(msg, "Invalid FTP configuration")
            return False

        #Transfer files
        self.ship_file(xml, 'report.xml',            ftp)
        self.ship_file(am,  'account_move.txt',      ftp)
        self.ship_file(aml, 'account_move_line.txt', ftp)
        self.ship_file(aa,  'account_account.txt',   ftp)

        #report and exit positively
        ftp.close()
        final_msg = "File transfer for Schuiteman / Peacock succesfull"
        _logger.info(final_msg)
        config.latest_run     = datetime.datetime.utcnow().strftime('UTC %Y-%m-%d %H:%M:%S ')
        config.latest_status  = msg+final_msg
        config.write({})
        return True

    def add_element(self, node, dict, tag ) :
        new_node  = etree.Element(tag)
        node.append(new_node)
        for key, value in dict.iteritems() :
            element = etree.Element(key)
            new_node.append(element)
            if type(value) in [str, unicode, int, float] :
                element.text = str(value)
            elif type(value)==bool :
                element.text = str(value)
            elif key.endswith('ids') :
                n=0
                for v in value :
                    sub_node = etree.Element('_'+str(n))
                    element.append(sub_node) 
                    sub_node.text = str(v)
                    n += 1
            elif type(value)==tuple and type(value[0])==int and type(value[1])==unicode :
                sub_node = etree.Element('id')
                element.append(sub_node) 
                sub_node.text = str(value[0])
                sub_node = etree.Element('name')
                element.append(sub_node) 
                sub_node.text = str(value[1])
            elif type(value)==tuple :
                n=0
                for v in value :
                    sub_node = etree.Element('_'+str(n))
                    element.append(sub_node) 
                    sub_node.text = str(v)
                    n += 1
            else : #object
                self.add_element(element, value, key)
        return True
	