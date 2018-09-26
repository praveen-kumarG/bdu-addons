# -*- coding: utf-8 -*-

import datetime, httplib, json, logging, pdb
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger(__name__)

class PubbleConfig(models.Model):
    _name        = 'pubble.config'
    _description = 'Connection info to Pubble issue data'
    server  	 = fields.Char(string='Server',help="servername, without protocol, e.g. ws.pubble.nl" )
    method		 = fields.Char(string='Method and query',help="method with start slash, e.g. /dir/api?date=20180101")
    
    latest_issue   = fields.Date(string='Latest issue',   help="Latest issue processed by Pubble connector")
    latest_run     = fields.Char(string='latest_run',     help="Date of latest run of Pubble connector")
    latest_success = fields.Char(string='Latest success', help="Youngest date when Pubble connector was successfully retrieving info")
    latest_status  = fields.Char(string='Latest status',  help="Status of latest run")
    latest_reason  = fields.Char(string='Latest reason',  help="Reason of status code of latest run")
    
    begin		   = fields.Date(string='Begin', help="begindatum van datumrange in de vorm yyyy-mm-dd")
    end 		   = fields.Date(string='End',  help="einddatum van datumrange in de vorm yyyy-mm-dd", widget="date")
    
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
                    "res_model":"pubble.config",
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

    def ms_datetime_to_python_date(self, ms_datetime_string):
        #format received is  /Date(1519945200000+0100)/
        startpos   = ms_datetime_string.find("/Date(") + 6
        endpos     = ms_datetime_string.find("+")
        eastern_hemisphere = True
        if endpos==-1:
            endpos = ms_datetime_string.find("-")
            eastern_hemisphere = False
        seconds    = long(ms_datetime_string[startpos:endpos-3])
        tz_secs    = int(ms_datetime_string[endpos+1:endpos+3])*3600 + int(ms_datetime_string[endpos+3:endpos+5])*60
        if eastern_hemisphere :
            local_secs = seconds+tz_secs
        else :
            local_secs = seconds-tz_secs
        date       = datetime.date.fromtimestamp(local_secs)
        return date


    @api.multi
    def automated_do_collect(self):
        configurations = self.search([])
        if not configurations :
            _logger.info("Cannot run automated_do_collect. Need a valid configuration")
            return False
        else :
            self = configurations[0]
            self.begin = datetime.date.today()
            self.end   = datetime.date.today()
            self.write({})
            return self.do_collect()

    
    @api.multi 
    def do_collect(self):

        #collect data based on config 	    
        config = self[0] 
        if not config.latest_issue :
            most_recent=datetime.date(1970,1,1)
        else :
            most_recent=datetime.datetime.strptime(config.latest_issue,DEFAULT_SERVER_DATE_FORMAT).date()

        if not config.begin or not config.end :
            raise ValidationError("Please provide begin and end date")
            return False

        conn   = httplib.HTTPSConnection(config.server.strip())
        api    = config.method.strip()
        api    = api.replace("$begin",config.begin).replace("$end",config.end)

        conn.request("GET", api)
        response = conn.getresponse()
        answer   = response.read()
        status   = response.status
        reason   = response.reason
        conn.close()	
        
        if (reason == "OK") :

            #lookup values and other init
            title_accounts = self.env['sale.advertising.issue'].search([('parent_id','=', False)])
            _logger.info("sale.advertising.issue titles found : ")
            for t in title_accounts :
                _logger.info("content of default_note : %s", t['default_note'])
            pubble_kpis = self.env['mis.pubble.kpi']

            json_anwser = json.loads(answer)
            d = {}
            message = ""
            
            #flatten json and write every page to new or existing records
            for title_summary in json_anwser :
                d['title']      = title_summary['titel']

                #keep track of latest updated issue
                issue_date = self.ms_datetime_to_python_date(title_summary['datum'])
                d['issue_date'] = issue_date

                if issue_date>most_recent :
                    most_recent = issue_date
                
                #analytic accounnt and company via sale.advertising.issue
                title_account   = title_accounts.search([('parent_id','=', False),('default_note','=',d['title'])])
                if len(title_account)==1:
                    d['title_code'] = title_account[0]['code']
                    d['company_id'] = title_account[0].analytic_account_id.company_id.id
                    d['analytic_account_id'] = title_account[0].analytic_account_id.id
                    ou_ids = self.env['account.analytic.account'].search([('id','=',d['analytic_account_id'])])
                    d['operating_unit_id'] = ou_ids.operating_unit_ids.id
                else:
                    message += ",<br>"+d['title']+" not/double in ad issues"
                    d['title_code'] = ""
                    d['company_id'] = ""
                    d['analytic_account_id'] = ""

                #register every page to facilitate manual adaption
                pages           = title_summary['paginas']  

                for page in pages :
                    d['page_nr']      = int(page['paginaNummer'])

                    d['page_type']=page.get('paginaType', 'n.a.') 
                    if d['page_type'] is None :
                        d['page_type']='n.a.'
                    
                    d['page_style']   = page.get('paginaStramien','n.a.')
                    if d['page_style'] is None :
                        d['page_style']='n.a.'


                    d['is_spread'] = page['isSpread']

                    #Geen overervig = 0
                    #Overerving van toepassing, pagina is bron = 1
                    #Overerving van toepassing, pagina is doel = 2
                    #Overerving van toepassing, pagina is wissel = 3
                    if page['overerving']== 3 :
                        d['is_inherited'] = True
                    else :
                        d['is_inherited'] = False 

                    d['ad_count']   = int(page['advertentieAantal'])
                    
                    if d['page_type']=="Advertentie" :
                        d['ad_page'] = 1 #+ self.conditional_ad(d['is_spread'], 1)
                        d['ed_page'] = 0
                    else :
                        d['ad_page'] = 0
                        d['ed_page'] = 1 #+ self.conditional_ad(d['is_spread'], 1)
                    
                    existing_recs = pubble_kpis.search([('title',     '=', d['title']     ),
                                                        ('issue_date','=', d['issue_date']),
                                                        ('page_nr',   '=', d['page_nr']   )
                                    ])
                    
                    if len(existing_recs)==0 :
                        pubble_kpis.create(d)
                    else :
                        d['issue_date']=existing_recs[0].issue_date
                        existing_recs[0].write(d)

            #leave testimonial with config info
            config.latest_issue   = most_recent
            config.latest_run     = datetime.datetime.utcnow().strftime('UTC %Y-%m-%d %H:%M:%S ')+message
            config.latest_success = datetime.date.today()
            config.latest_status  = status
            config.latest_reason  = reason
            config.write({})
            _logger.info("Successfull import for dates between %s and %s", config.begin, config.end)
            return True
        else :
            config.latest_run     = datetime.date.today()
            config.latest_status  = status
            config.latest_reason  = reason
            config.write({})
            _logger.info("Error while trying to import Pubble data")
            return False

	