# -*- coding: utf-8 -*-

import datetime, httplib, json, logging, pdb
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger(__name__)

class PubbleProductionConfig(models.Model):
    _name          = 'pubble.production.config'
    _description   = 'Connection info to Pubble production data API'

    server         = fields.Char(string='Server',help="servername, without protocol, e.g. ws.pubble.nl" )
    method         = fields.Char(string='Method and query',help="method and query, e.g. /dir/api?date=20180101")
    
    latest_success = fields.Date(string='Latest success', help="Latest successfull run")
    latest_week    = fields.Char(string='Latest week',   help="Latest week successfully processed ")
    
    latest_run     = fields.Char(string='latest run',     help="Date of latest run (successfull or not")
    latest_status  = fields.Char(string='Latest status',  help="Status of latest run")
    latest_reason  = fields.Char(string='Latest reason',  help="Reason of status code of latest run")
    
    begin          = fields.Date(string='Begin', help="From date with format yyyy-mm-dd")
    end            = fields.Date(string='End',  help="To date with format yyyy-mm-dd", widget="date")
    
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
                    "res_model":"pubble.production.config",
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
            _logger.info("Cannot run automated_do_collect of reverse billing info. Need a valid configuration")
            return False
        else :
            config = configurations[0]
            #get info for last week up until today
            weekday       = datetime.date.today().isoweekday() #mo=1...su=7 
            config.begin  = datetime.date.today()-datetime.timedelta(days=7+weekday)
            config.end    = datetime.date.today()
            config.write({})
            return self.do_collect()

    
    @api.multi 
    def do_collect(self):
        config = self.env['pubble.production.config'].search([])[0] 
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
            adv_issues   = self.env['sale.advertising.issue'].search([('parent_id','!=', False)])
            current_data = self.env['pubble.production.data'].search([])
            conversions  = self.env['pubble.product.conversion'].search([])

            json_anwser = json.loads(answer)
            batch=json_anwser['ArticleBatch']
            articles= batch['articles']

            message = ""


            for article in articles :
                #article specific info
                article_id         = article['id']
                author             = article['auteur']
                working_title      = article['werktitel']
                article_date       = self.ms_datetime_to_python_date(article['gemaakt'])
                url                = article['pubbleUrl']
                remark             = article['werktitel']
                #related info
                order_lines        = article['opdrachten']
                publications       = article['publicaties']
                billing_lines      = article['selfBillingRegels']

                #order_lines details who gave the order(s)
                commissioned_by = ""
                commissioned_by_xxl = ""
                for order in order_lines :
                    if commissioned_by=="" :
                        commissioned_by     = order['gemaaktDoor']
                        commissioned_by_xxl = order['gemaaktDoor']+" aan "+order['toegewezenAan']
                    else :
                        commissioned_by     += ",\n"+order['gemaaktDoor']
                        commissioned_by_xxl += ",<br/>"+order['gemaaktDoor']+" aan "+order['toegewezenAan']
                    if order['productCode'] != False and order['productCode'] != "None" and order['productCode'] != "" and order['productCode'] != "null":
                        commissioned_by_xxl += " ("+str(order['productCode']) +")"


                #other publications as informational text added
                publications_as_text = self.pretty_publications(publications) 

                #First publication steers cost taking title and moment
                #Locked after being processed, so final consumption of data is done at the end
                title      = False
                issue_date = False
                titles     = False
                year       = False
                week       = False
                if (len(publications)>0) :
                    compare_date= datetime.date(2999,12,31)
                    for publication in publications :
                        current_issue_date = self.ms_datetime_to_python_date(publication['publicatieDatum'])
                        if current_issue_date < compare_date :
                            title = publication['publicatieCode']
                            issue_date = current_issue_date
                            year = issue_date.isocalendar()[0]
                            week = issue_date.isocalendar()[1]
                            compare_date=current_issue_date
                        if titles :
                            titles += ",\n"+publication['publicatieCode']
                        else:
                            titles  = publication['publicatieCode']

                #get accounting info
                if (title) :
                    ids = self.ids_by_issue_and_date(adv_issues, title, issue_date)
                else :
                    ids = {}

                #all billing lines related to article consolidated as accompanying text
                related_costs = self.pretty_billing_lines(billing_lines) 

                for billing_line in billing_lines :
                    #billing line becomes record with 1 article as parent and sibling orders and publications
                    record = {}
                    revbil_msg = ""
                    
                    #skip reverse billing line if bdu, or user generated content or not published and not approved
                    credit   = billing_line['credit']
                    if credit.find('@bdu.nl') > -1 :
                        continue
                    if credit.find('Ingezonden via website') > -1 :
                        continue
                    pubble_product  = billing_line['productCode']
                    if pubble_product.find('tekst') > -1 and len(publications)==0 :
                        continue

                    #search freelancer
                    searchresult    = self.findPartnerByEmail(billing_line['credit'])
                    freelancer      = searchresult['partner']
                    if not freelancer and message.find(searchresult['message'])==-1 and searchresult['message'].find('@bdu.nl')==-1 :
                        message   += searchresult['message']
                        revbil_msg = searchresult['message']

                    #other info
                    pubble_count    = billing_line['aantal']
                    date2           = self.ms_datetime_to_python_date(billing_line['gemaaktOp'])
                    odoo_product    = self.convert_2_odoo_product(conversions,pubble_product, pubble_count)
                    if freelancer and odoo_product['count'] and odoo_product['product_id'] :
                        unit_price  = freelancer.property_product_pricelist.get_product_price(odoo_product['product_id'], odoo_product['count'], freelancer)
                        total_price = unit_price * odoo_product['count']
                    else :
                        unit_price  = 0
                        total_price = 0

                    #create record
                    record['name']                = billing_line['referentie']
                    record['issue_date']          = issue_date.strftime('%Y-%m-%d')
                    record['article_id']          = article_id
                    if odoo_product['product_id'] :
                       record['product_id']       = odoo_product['product_id'].id
                    else :
                        record['product_id']      = False
                    record['count']               = odoo_product['count']
                    record['unit_price']          = unit_price
                    record['total_price']         = total_price
                    record['pubble_product']      = pubble_product
                    record['pubble_count']        = pubble_count
                    if freelancer :
                        record['freelancer']      = freelancer.id
                    else:
                        record['freelancer']      = False
                    record['url']                 = url  
                    record['remark']              = remark
                    record['titles']              = titles
                    record['publications']        = publications_as_text
                    record['related_costs']       = related_costs
                    record['year']                = year
                    record['week']                = week
                    if ids['issue_id'] :
                        record['title']           = title
                        record['issue_id']        = ids['issue_id']
                    else :
                        record['title']           = False
                        record['issue_id']        = False
                    record['analytic_account_id'] = ids['analytic_account_id']
                    record['operating_unit_id']   = ids['operating_unit_id']
                    record['commissioned_by']     = commissioned_by
                    record['commissioned_by_xxl'] = commissioned_by_xxl
                    record['message']             = revbil_msg   
                    if odoo_product['product_id'] == False :
                        record['message'] += "Pubble product/count could not be converted. Check conversion data.<br/>"
                    if freelancer == False :
                        record['message'] += "Email address "+credit+" not found in Odoo. No payment possible.<br/>"

                    #search for existing record
                    existing_recs = current_data.search([  ('name', '=', record['name']) ])

                    #if freelancer not in Odoo then skip record
                    if freelancer :
                        #create if not present else adapt to situation
                        if len(existing_recs)==0 :
                            current_data.create(record)
                        else :
                            #changes after accepted and processed are refused
                            current=existing_recs[0]
                            if current.processed :
                                record={}
                                record['message'] = "Update after being processed is refused"
                                current.write(record)
                            elif current.accepted :
                                record={}
                                record['message'] = "Update after being accepted is refused"
                                current.write(record)
                            else :
                                #update
                                existing_recs[0].write(record)

            #leave testimonial with config info
            config.latest_success = datetime.date.today()            
            config.latest_week    = str(datetime.date.today().isocalendar()[0])+"-"+str(datetime.date.today().isocalendar()[1])
            
            config.latest_run     = datetime.datetime.utcnow().strftime('UTC %Y-%m-%d %H:%M:%S ')+"<br/>"+message
            config.latest_status  = status
            config.latest_reason  = reason
            config.write({})
            _logger.info("Successfull import for dates between %s and %s", config.begin, config.end)
            return True

        else :
            config.latest_run     = datetime.datetime.utcnow().strftime('UTC %Y-%m-%d %H:%M:%S ')+" stopped because of error."
            config.latest_status  = status
            config.latest_reason  = reason
            config.write({})
            _logger.info("Error while trying to import Pubble data")
            return False

    @api.multi
    def findPartnerByEmail(self, email_address) :
        partners = self.env['res.partner'].search([('email','=',email_address)])
        
        if len(partners)==1 :
            if partners[0].supplier :
                return {'message' : '', 'partner' : partners[0]}
            else : 
                return {'message' : "Found one partner with email address "+email_address+", but this is not a supplier<br/>",
                        'partner' : False}
        
        elif len(partners)>1 :
            return {'message' : "Multiple entries for "+email_address+", please deduplicate<br/>",
                    'partner' : False}

        else :
            return {'message' : "email address "+email_address+" not found<br/>",
                    'partner' : False}


    @api.multi 
    def convert_2_odoo_product(self, conversions, pubble_product, pubble_count) :
        products=conversions.search([  ('pubble_product_name','=',   pubble_product),
                                       ('pubble_count_min',   '<=',  pubble_count),
                                       ('pubble_count_max',   '>=',  pubble_count)
                                     ])
        if len(products)==1 :
            product=products[0]
            if product.count_conversion :
                count = 1
            else :
                count = pubble_count
            return {'product_id':product.odoo_product_id,'count':count}
        else :
            return {'product_id':False,'count':False}



    @api.multi
    def ids_by_issue_and_date(self, adv_issues, title, issue_date) :
        #analytic account and company via sale.advertising.issue
        result={'issue_id':False, 'company_id':False, 'analytic_account_id':False, 'operating_unit_id':False}
        issues = adv_issues.search([('parent_id', '=', title),
                                    ('issue_date','=', issue_date.strftime('%Y-%m-%d') )
                                   ])    
        if len(issues)==1:
            result['issue_id']            = issues[0]['id']
            result['company_id']          = issues[0].analytic_account_id.company_id.id
            result['analytic_account_id'] = issues[0].analytic_account_id.id
            ou_ids = self.env['account.analytic.account'].search([('id','=',result['analytic_account_id'])])
            result['operating_unit_id']   = ou_ids.operating_unit_ids.id
        return result

    @api.multi
    def pretty_publications(self,publications) :
        s = ""
        for pub in publications :
            s += (pub['publicatieCode'] or "")
            s += ", "+self.ms_datetime_to_python_date(pub['publicatieDatum']).strftime("%Y-%m-%d")
            s += ", page "+str(pub['pagina'])
            s += " (id : "+str(pub['id'])
            s += ", "+str(pub['aantalTekens'])+" characters)" #<br/>"
            s += "<ul>"
            for photo in pub['gepubliceerdeFotos'] :
                if photo['origineleNaam'] :
                    pname=photo['origineleNaam']
                else :
                    pname="click here to see"
                s += "<li><a href='>"+str(photo['url'])+"'>"+pname+"</a>"
                s += " ("+photo['genomenDoor']
                s += ", "+self.ms_datetime_to_python_date(photo['genomenOp']).strftime("%Y-%m-%d")+")"
                #s += "Id :"+str(photo['id'])
                #if photo['fotoCredit'] :
                #    s += ", credit : "+photo['fotoCredit']
                #if photo['opmerkingen'] :
                #    s += ", remark : "+photo['opmerkingen']
                s += "</li>"
            s += "</ul>"
        s += ""
        return s

    @api.multi
    def pretty_billing_lines(self,billing_lines) :
        s = ""
        for line in billing_lines :
            s += line['credit']
            s += ", "+self.ms_datetime_to_python_date(line['gemaaktOp']).strftime("%Y-%m-%d")
            s += ": <b>"+str(line['aantal'])
            s += " x "+line['productCode']+"</b>"
            s += " (ref:"+str(line['referentie'])+")"
            s += "<br/>"
        s += ""
        return s



    @api.multi
    def pretty_json(self,text) :
        s = json.dumps(text, indent=4, sort_keys=True)
        s = s.replace("\n","<br />\n")
        s = s.replace("    ","\t")
        return s


    