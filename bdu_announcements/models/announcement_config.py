# -*- coding: utf-8 -*-
import pdb
import base64, datetime, httplib, json, logging, pdb, requests, urllib
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)

class AnnouncementConfig(models.Model):
    _name          = 'announcement.config'
    _description   = 'Connection info for Announcement API interface'
    server  	   = fields.Char(string='Server',help="servername, including protocol, e.g. https://prod.barneveldsekrant.nl" )
    method		   = fields.Char(string='Method and query',help="method with start slash, e.g. /api/v1")
    user           = fields.Char(string='User')
    password       = fields.Char(string='Password')
    ad_class       = fields.Many2one('product.category', 'Advertising Class')

    oldest_synced  = fields.Datetime(string='Oldest synced',   help="Oldest ordeline update successfully synced")
    latest_run     = fields.Char(string='Latest run',     help="Date of latest run of Announcement connector")
    latest_success = fields.Char(string='Latest success', help="Youngest date when connector was shipping successfully")
    latest_status  = fields.Char(string='Latest status',  help="Status of latest run")
    latest_reason  = fields.Char(string='Latest reason',  help="Reason of status code of latest run")
    
    begin		   = fields.Date(string='Begin', help="Begin date of date range in format yyyy-mm-dd")
    
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
                    "res_model":"announcement.config",
                    "view_type":"form",
                    "view_mode":"form",
                    "res_id":configuration,
                    "target":"inline",
        }
        return action

    @api.multi
    def save_config(self):
        self.write({}) #{"server": server, "method":method, "query" : query})
        return True

    def conditional_ad(self, boolean_condition, value_to_ad):
        if boolean_condition :
            return value_to_ad
        else :
            return 0

    #hook for automated actions
    @api.multi
    def automated_run(self):
        configurations = self.search([])
        if not configurations :
            _logger.info("Cannot start automated_run. Need a valid configuration")
            return False
        else :
            #start with previous end
            self = configurations[0]
            if not config.oldest_synced :
                 oldest_synced = datetime.datetime(1970,1,1,0,0)
            self.begin = datetime.datetime.strptime(config.oldest_synced,DEFAULT_SERVER_DATETIME_FORMAT).date()
            self.write({})
            return self.do_send()

    #loop started by automated run (above) or send button push
    @api.multi 
    def do_send(self):
        #collect config data to run with 	    
        config = self[0] 
        if not config.oldest_synced :
            oldest_synced = datetime.datetime(1970,1,1,0,0)
        else :
            oldest_synced = datetime.datetime.strptime(config.oldest_synced,DEFAULT_SERVER_DATETIME_FORMAT)

        if not config.begin :
            raise ValidationError("Please provide a begin date")
            return False
        
        #get changed orderlines since oldest_non_synced
        announcements=self.env['sale.order.line'].search([('custom_orderline', '=', 'Announcement'),\
                                                          ('write_date', '>', config.begin+" T00:00:00")]).\
                      sorted(key = lambda r : r.write_date)

        #abandon early if no changes
        if not announcements :
            config.latest_run     = datetime.date.today()
            config.latest_status  = "N.A."
            config.latest_reason  = "No orderlines changed since "+oldest_synced.strftime("%Y-%m-%d T%H:%M%S")
            config.write({})
            _logger.info("No new announcements to sync to website")
            return True

        #init loop
        all_good      = True
        ok_recs       = 0
        errors        = 0
        no_material   = 0
        status        = ""
        message       = ""
        oldest_synced = datetime.datetime.strptime(config.begin+" T00:00:00", "%Y-%m-%d T%H:%M:%S")

        #loop through changed orderlines
        for announcement in announcements :
            result = self.send_orderline(announcement)
            if result == "no material" :
                all_good       = False
                no_material   += 1
                message       += "<br>"+str(announcement.order_id.name)+" - "+str(announcement.id)+" : No material. Not sent."
            elif result == "ok" :
                oldest_synced  = announcement['write_date']
                ok_recs       += 1
                message       += "<br>"+str(announcement.order_id.name)+" - "+str(announcement.id)+" : Synced"
            else : #bad response
                all_good       = False
                errors        += 1
                status         = result.split(',')[1]
                message       += "<br>"+str(announcement.order_id.name)+" - "+str(announcement.id)+" : Bad response, reason = "+result.split(',', 2)[2]


        #leave testimonial of run result
        if all_good :
            config.oldest_synced  = oldest_synced
            config.latest_run     = datetime.datetime.utcnow().strftime('UTC %Y-%m-%d %H:%M:%S ')
            config.latest_success = datetime.date.today()
            config.latest_status  = "Last record processed : "+result
            config.latest_reason  = "Sync OK"
            config.write({})
            _logger.info("Successfull shipment of %d announcement orderlines created/changed after %s T00:00:00",\
                         len(announcements), config.begin)
            return True
        else :
            config.oldest_synced  = oldest_synced
            config.latest_run     = datetime.datetime.utcnow().strftime('UTC %Y-%m-%d %H:%M:%S ')
            config.latest_status  = status
            prologue              = "%d lines without material. %d errors. %d records OK. Oldest_non_synced kept at first error/no material." % (no_material, errors, ok_recs)
            config.latest_reason  = prologue+message
            config.write({})
            _logger.info("Finished processing with errors. See connector page for details.")
            return False

    #method to be called by order update or loop (above)
    @api.multi 
    def send_orderline(self, orderline):
        #use config to prep api call      
        config = self[0] 
        url         = config.server.strip()+config.method.strip()
        b_auth      = bytes(config.user+":"+config.password)
        headers     = {'authorization': "Basic " + base64.b64encode( b_auth),
                       'cache-control': "no-cache",
                       'content-type' : "application/x-www-form-urlencoded",
                      }

        #only send if url_to_material available or if publication cancelled
        if orderline.product_uom_qty !=0 and not orderline.url_to_material :
            return "no material"
        else :
            payload={}
            payload['source']        = "Odoo"
            payload['nr']            = orderline.id
            payload['url2material']  = orderline.url_to_material

            if orderline.order_id.state == 'sale' :
                payload['count']     = str(int(orderline.product_uom_qty)) 
            else :
                payload['count']     = "0"

            #custom orderline variables
            payload['firstname']     = orderline.announcement_firstname
            payload['lastname']      = orderline.announcement_lastname
            payload['city']          = orderline.announcement_city
            payload['startdate']     = orderline.announcement_from_date   #target format yyyy-mm-dd
            payload['enddate']       = orderline.announcement_to_date     #target format yyyy-mm-dd
            
            publications=[]
            for issue in orderline.announcement_adv_issue_ids :
                publication = {}
                publication['title'] = issue.parent_id.code
                publication['date']  = issue.issue_date
                publications.append(publication)
            payload['publications'] = json.dumps(publications)

            #send it
            #response=requests.post(url, data=payload, headers=headers)
            response = requests.request("POST", url, data=payload, headers=headers)
            if response.status_code == requests.codes.ok :  # equal 200 ok
                return "ok"
            elif response.status_code == 502 :
                return "bad response,"+str(response.status_code)+", "+response.content
            else:
                #pdb.set_trace()
                msg=str(response.json()['message'])
                return "bad response,"+str(response.status_code)+", "+msg


	