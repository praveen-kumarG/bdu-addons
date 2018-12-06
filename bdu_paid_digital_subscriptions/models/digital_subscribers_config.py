# -*- coding: utf-8 -*-

import datetime, ftputil,  ftputil.session, httplib, json, logging, pdb, requests, urllib
from lxml import etree 
from tempfile import TemporaryFile
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger(__name__)

class DigitalSubscribersConfig(models.Model):
    _name          = 'digital.subscribers.config'
    _description   = 'Connection info for communicating digital subscribers'
    server  	   = fields.Char(string='Server',         help="FTP server" )
    directory	   = fields.Char(string='Server subdir',  help="Directory starting with slash, e.g. /api/v1, or empty")
    tempdir        = fields.Char(string='Local temp dir', help="Local temporary directory. e.g. /home/odoo")
    user           = fields.Char(string='User')
    password       = fields.Char(string='Password')
    offset_days    = fields.Integer(string='Offset in days')
    subscriber_ref = fields.Selection([('new','Only Odoo internal reference'),
                                       ('old','Use Zeno or Baarn when available')
                                       ],string='Subscriber ref.', default='old')

    latest_run     = fields.Char(string='Latest run',     help="Date of latest run of Announcement connector")
    latest_status  = fields.Char(string='Latest status',  help="Log of latest run")
    
    active_date	   = fields.Date(string='Active on',    help="Date for which subscribers should be active in format yyyy-mm-dd")
    
    #show only first record to configure, no options to create an additional one
    @api.multi
    def default_view(self):
        configurations = self.search([])
        if not configurations :
            server = "bdu.nl"
            self.write({'server' : server})
            configuration = self.id
            _logger.info("digital subscribers configuration created")
        else :
            configuration = configurations[0].id
        action = {
                    "type":"ir.actions.act_window",
                    "res_model":"digital.subscribers.config",
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

    def ship_file(self, msg, filename, conn):
        config = self[0]
        try:
            _logger.info("Transfering " + filename)
            if config.directory :
                target = str(config.directory) + '/' + filename
            else :
                target = '/' + filename
            source = config.tempdir + '/' + filename
            conn.upload(source, target)
            return True
        except Exception, e:
            self.log_exception(msg,"Transfer failed, quiting...., error"+str(e))
            return False



    @api.multi
    def automated_run(self):
        configurations = self.search([])
        if not configurations :
            #cannot use local method because there is no record
            _logger.exception(msg, "Cannot start automated_run. Need a valid configuration")
            return False
        else :
            #start normal with today plus offset in days as active date
            self = configurations[0]
            self.active_date = datetime.date.today()+datetime.timedelta(days=self.offset_days)
            self.write({})
            return self.do_send()

    
    @api.multi 
    def do_send(self):	
        msg    = ""    
        config = self[0] 
        if not config :
            self.log_exception(msg, "No configuration found. <br>Please configure digital subscribers connector.")
            return False
       
        if not config.active_date :
            #raise ValidationError("Please provide a valid date")
            self.log_exception(msg, "Program not started. <br>Please provide a valid date")
            return False

        if not config.server or not config.user or not config.password or not config.tempdir :
            #raise ValidationError("Missing configuration data. Please correct.")
            self.log_exception(msg,"Program not started. <br>Please provide a valid server/user/password/tempdir configuration")
            return False
        
        #calc begin and end date
        active_date   = datetime.datetime.strptime(config.active_date,DEFAULT_SERVER_DATE_FORMAT).date()

        #eligeble titles
        titles = self.env['sale.advertising.issue'].search([('parent_id','=',False),('digital_paywall','=',True)])
        if len(titles)==0 :
            self.log_exception(msg, "No titles with a paywall. Program terminated.")
            return False
        td = []
        for title in titles :
            td.append(str(title.name))

        #digital subscriptions
        orderlines = self.env['sale.order.line']
        domain = [
            ('start_date', '<=', self.active_date),
            ('end_date', '>=', self.active_date),
            #('company_id', '=', self.company_id.id),
            ('subscription', '=', True),
            ('state', '=', 'sale'),
            ('title', 'in', td),
            #('product_template_id.digital_subscription', '=', True),
        ]
        digital_subscriptions = orderlines.search(domain).sorted(key=lambda r: r.order_id.partner_shipping_id) 
        if len(digital_subscriptions)==0 :
            self.log_exception(msg, "No subscriptions with a paywall. Program terminated.")
            return False

        #temp file
        subscribers_list ={}

        for dc in digital_subscriptions :
            s_nr = dc.order_id.partner_shipping_id.ref
            if config.subscriber_ref == 'old' :
                if dc.order_id.partner_shipping_id.zeno_id :
                    s_nr = dc.order_id.partner_shipping_id.zeno_id
                if dc.order_id.partner_shipping_id.afas_id :
                    s_nr = dc.order_id.partner_shipping_id.afas_id
            if s_nr in subscribers_list :
                if subscribers_list[s_nr]['titles'].find(str(dc.title.name)) == -1 :
                    subscribers_list[s_nr]['titles'] += ', '+str(dc.title.name)
                #else double entry, no need to add
            else :
                subscribers_list[s_nr] = {'zip':str(dc.order_id.partner_shipping_id.zip), 'titles':str(dc.title.name)}

        # Initiate File Transfer Connection
        try:
            port_session_factory = ftputil.session.session_factory(port=21, use_passive_mode=True)
            ftp = ftputil.FTPHost(config.server, config.user, config.password, session_factory = port_session_factory)
        except Exception, e:
            self.log_exception(msg, "Invalid FTP configuration")
            return False
        
        #chop into 10k records max and ship
        n     = 0
        f_nr  = 1
        out   = config.tempdir+"/digital_subscribers_part"+str(f_nr)+".csv"
        f_out = open(out, "w")
        for subscriber in subscribers_list :
            line = str(subscriber)+','+subscribers_list[subscriber]['zip']+',,"'+subscribers_list[subscriber]['titles']+'"\n'
            n += 1
            if n<=10000 :
                f_out.write(line)
            else :
                f_out.close()
                if not self.ship_file(msg, "digital_subscribers_part"+str(f_nr)+".csv", ftp) :
                    return False
                f_nr += 1
                n     = 1
                out   = config.tempdir+"/digital_subscribers_part"+str(f_nr)+".csv"
                f_out = open(out,"w")
                f_out.write(line)
        f_out.close()
        if not self.ship_file(msg, "digital_subscribers_part"+str(f_nr)+".csv", ftp) :
            return False
        ftp.close()
        #todo: remove main file(s)

        #report and exit positively
        final_msg = "File transfer for digital subscribers succesfull"
        _logger.info(final_msg)
        config.latest_run     = datetime.datetime.utcnow().strftime('UTC %Y-%m-%d %H:%M:%S ')
        config.latest_status  = msg+final_msg
        config.write({})
        return True


	