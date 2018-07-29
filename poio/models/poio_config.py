# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import ftputil
import ftputil.session
from odoo.exceptions import UserError
import logging
import re
import time

from unidecode import unidecode

import os
import base64
import xml.etree.ElementTree as ET

import csv

_logger = logging.getLogger(__name__)


class POIOConfig(models.Model):
    _name = 'poio.config'

    o_server     = fields.Char(string="Server", copy=False)
    o_user       = fields.Char(string="Login", copy=False)
    o_password   = fields.Char(string="Password", copy=False)
    o_status     = fields.Char(string="Status", copy=False)

    work_dir   = fields.Char(string="Local work directory", copy=False, help="Local download directory excluding /in and /done")
    
    m_server     = fields.Char(string="Server", placeholder='Material server name excluding protocol and portnr', copy=False)
    m_user       = fields.Char(string="Login", copy=False)
    m_password   = fields.Char(string="Password", copy=False)
    m_status     = fields.Char(string="Status", copy=False)
    
    channel      = fields.Many2one('mail.channel', ondelete='set null', string="Channel", index=True)
    partner_am   = fields.Many2one('res.partner', ondelete='set null', string="Account manager", index=True)
    partner      = fields.Many2one('res.partner', ondelete='set null', string="Partner", index=True)

    discount_reason  = fields.Many2one('res.partner', ondelete='set null', string="Discount_reason", index=True)  
    sector           = fields.Many2one('res.partner.sector', ondelete='set null', string="Sector", index=True) 

    order_prefix     = fields.Char(string="Order prefix", copy=False)
    orderline_prefix = fields.Char(string="Orderline prefix", copy=False)

    def remove_non_ascii(self, t):
        return unidecode(unicode(t, encoding = "utf-8"))

    #show only first record to configure, no options to create an additional one
    @api.multi
    def default_view(self):
        configurations = self.search([])
        if not configurations :
            o_server = "URL excluding protocol. E.g. : ftp.mycompany.nl"
            self.write({'o_server':o_server})
            configuration = self.id
        else :
            configuration = configurations[0].id
        action = {
                    "type":"ir.actions.act_window",
                    "res_model":"poio.config",
                    "view_type":"form",
                    "view_mode":"form",
                    "res_id":configuration,
                    "target":"inline",
        }
        return action 

    #trim spaces, they are not noticed by user and introduce errors
    @api.onchange('o_server')
    def onchange_o_server_dir(self):
        self.o_server = self.o_server.strip()

    #trim spaces, they are not noticed by user and introduce errors
    @api.onchange('m_server')
    def onchange_m_server_dir(self):
        self.m_server = self.m_server.strip()

    #include slashes in dir names when absent
    @api.onchange('work_dir')
    def onchange_work_dir(self):
        self.work_dir = self.set_slashes(self.work_dir)

    #include slashes in dir names when absent
    def set_slashes(self,text):
        if text and not text.endswith('/'):
            text = text + '/'
        if text and not text.startswith('/'):
            text = '/' + text
        return text
    
    #buttons
    @api.multi
    def test_order_connection(self):
        msg = self.test_connection(self.o_server, self.o_user, self.o_password)
        self.write({'o_status' : msg})
        self._cr.commit()
        return True

    @api.multi
    def test_material_connection(self):
        msg = self.test_connection(self.m_server, self.m_user, self.m_password)
        self.write({'m_status' : msg})
        self._cr.commit()
        return True

    @api.multi
    def test_connection(self, server, user, password):
        msg = ""
        try:
            port_session_factory = ftputil.session.session_factory(port=21) #self.port)
            ftp = ftputil.FTPHost(server, user, password, session_factory = port_session_factory)
            msg = 'OK'
        except Exception, msg:
            msg = "Invalid configuration / network fault"
        return msg 


    @api.multi
    def save_config(self, vals):

        if not self.o_status :
            msg = 'Configuration saved'
        else :
            msg = self.o_status.replace(' configuration saved', '')+' configuration saved'
        #+self.env.context.get(noactive_id,"no active_id")
        self.write({'o_status' : msg})

        if not self.m_status :
            msg = 'Configuration saved'
        else :
            msg = self.m_status.replace(' configuration saved', '')+' configuration saved'
        #+self.env.context.get(noactive_id,"no active_id")
        self.write({'m_status' : msg})

        self._cr.commit()
        return True



    @api.multi
    def do_job(self):
        #get new files
        try:
            if not self.get_files() :
                raise UserError("Could not collect Promille files")
                return False
        except Exception, e:
            raise UserError("Error while collecting Promille files")
            return False
        #process files (todo: customers, contacts, orders)    
        try:
            if not self.process_files() :
                raise UserError("Could not process Promille files")
                return False
        except Exception, e:
            raise UserError("Error while processing Promille files")
        #if succesful
        return True


    @api.multi
    def get_files(self):
        #get connection parameters
        configs = self.search([])
        config  = configs[0]
        if not config:
            _logger.exception("FTP Connection does not exist, please configure.")
            return False
        # Initiate File Transfer Connection
        try:
            port_session_factory = ftputil.session.session_factory(port=21)
            ftp = ftputil.FTPHost(config.o_server, config.o_user, config.o_password, session_factory = port_session_factory)
            msg = 'OK'
        except Exception, msg:
            _logger.exception("Invalid FTP configuration.")
            msg = "Invalid FTP configuration"
            return False
        #Transfer files
        try:
            for file in ftp.listdir(""):
                _logger.info("File to transfer : " + file)
                dest_path = str(config.work_dir + 'in/' + file)
                ftp.download(file, dest_path)
                #ftp.remove(file) 
            ftp.close()
        except Exception:
            _logger.warning("File transfer failed")
            msg = "File transfer failed"
            return False
        #if succesfull
        msg = "File transfer succesfull"
        return True

    @api.model
    def process_files(self, ids=None):
        #get connection parameters
        configs = self.search([])
        config  = configs[0]
        work_dir= config.work_dir
        channel = config.channel
        am      = config.partner_am.id

        status =   {'last_status'        : '',
                    'customer_files'     : 0,
                    'customers'          : 0,
                    'c_new'              : 0,
                    'c_found'            : 0,
                    'c_coc_match'        : 0,
                    'c_email_match'      : 0,
                    'c_name_zip_match'   : 0,
                    'c_name_phone_match' : 0,
                    'c_error'            : 0,
                    'c_messages'         : '' 
                    }

        try:
        # sort local path files based on creation date
            files = os.listdir(str(work_dir + 'in/'))
        except Exception, e:
            _logger.exception("POIO import file : %s" % str(e))
            return True

        #Customers
        t_start = time.strftime('%Y-%m-%d %H:%M')
        self.process_customer_files(work_dir, files, status)
        t_end   = time.strftime('%Y-%m-%d %H:%M')
        message =  _("Verslag verwerking van %d customer bestanden, van %s tot %s : <br>") % (status['customer_files'], t_start, t_end)
        if status['c_new']>0              : message += _("- %s nieuwe klanten<br>") % status['c_new']
        if status['c_found']>0            : message += _("- %s bestaande klanten in bestand (onveranderd)<br>") % status['c_found']
        if status['c_coc_match']>0        : message += _("- %s bestaande klanten uitgebreid middels KvK nr match<br>") % status['c_coc_match']
        if status['c_email_match']>0      : message += _("- %s bestaande klanten uitgebreid middels email match<br>") % status['c_email_match']
        if status['c_name_zip_match']>0   : message += _("- %s bestaande klanten uitgebreid middels naam + postcode + huisnummer match<br>") % status['c_name_zip_match']
        if status['c_name_phone_match']>0 : message += _("- %s bestaande klanten uitgebreid middels naam + telefoonnr match<br>") % status['c_name_phone_match']
        if (status['c_new'] +
            status['c_found']+
            status['c_found']+
            status['c_coc_match']+
            status['c_email_match']+
            status['c_name_zip_match']+
            status['c_name_phone_match'] ) ==0 : message += _("- geen records verwerkt<br>")  
        if len(status['c_messages'])>0    : message += _("Infoberichten: <br>%s") % status['c_messages']
        self.log(channel,message, "promille order interface")

        #Contacts
        #self.process_contact_files(work_dir, files)
        #self.process_order_files(work_dir, files)

        #return something nice
        _logger.info("POIO files processed")
        return "Happily done for you"

    def log(self, channel, message, from_party):        
        MailMessage = self.env['mail.message'].search([('id','=',channel.id)])
        message_dict = {
                        'res_id'       : channel.id,
                        'message_type' : 'email',
                        'email_from'   : from_party,
                        'subject'      : 'poio verwerkingsverslag',
                        'body'         : message,
                        #'channel_ids'  : channel,
                        'model'        : 'mail.channel',
                        'subtype_id'   : 1
                       }
        MailMessage.create(message_dict)
        return True

    #customers 

    def process_customer_files(self, work_dir, files, status):
        msg  = "Start processing " + str(len(files)) + " promille files.<br>"
        _logger.info(msg)
        #counters and message containers
        new = errors = email_match = name_match = 0
        email_matching_message = error_reporting = name_matching_message = new_report = ""
        #process only files starting with customer and ending with csv by using the csv module
        for filename in files:
            if not filename.startswith('customers_'): continue
            if not filename.endswith('.csv'): continue 
            status['customer_files'] += 1
            file = os.path.join(str(work_dir + 'in/'), filename)
            f = open(file,'rb')
            reader = csv.reader(f, delimiter=';')
            #line processing
            for customer in reader:
                if customer[0]!='Received': self.process_customer(customer, status)
            #cleanup
            f.close()  
            #todo: move file to done directory
        return status

    def process_customer(self, customer, status):
        status['customers'] +=1
        #defined by config or hard coded
        configs = self.search([])
        promille_config  = configs[0]
        sector        = promille_config.sector
        country_id    = 166 #Netherlands
        is_company    = 1
        lang          = "nl_NL"
        message_is_follower = 0
        is_customer   = 1
        property_payment_term_id = 0 #0=default, 1=direct betalen, ?=standard 15 days, ?=standard 30 days  
        trust         = "normal"

        #given by Promille
        tmg_nr        = customer[1]
        name          = customer[3]
        street_name   = customer[11]
        street_number = str(customer[12])
        street2       = customer[13]
        zipcode       = customer[14].replace(" ", "").upper()
        city          = customer[15]

        phone         = customer[23].replace(" ", "").replace("(", "").replace(")", "").replace("-", "")
        mobile        = customer[24].replace(" ", "").replace("(", "").replace(")", "").replace("-", "")
        email         = customer[25]
        website       = customer[27]
        if website=="http://" : website = ""
        coc_nr        = customer[30] 

        if customer[44]=="B002 BUREAU / Reklamebureau" : is_ad_agency=1
        else                                           : is_ad_agency=0

        btwnr = customer[32].replace(".", "")
        if not btwnr.startswith("NL") : btwnr = "NL"+btwnr
        if not re.match(r'NL[0-9]{9}B01', btwnr, re.I) : btwnr=""
        btwstring="\n- BTW nr            \t= "+customer[32]

        #keep all info in comment for reference
        comment    = "Originele partner-info vanuit Promille:"+\
                     "\n- Promille_id         \t= "   +tmg_nr+\
                     "\n- Naam                \t= "+name+\
                     "\n- Adres               \t= "+street_name+" "+street_number+" "+street2+", "+zipcode+" "+city+\
                     "\n- Telefoon            \t= "+phone+\
                     "\n- Mobiel              \t= "+mobile+\
                     "\n- Email               \t= "+email+\
                     "\n- website             \t= "+website+\
                     "\n- Email adres factuur \t= "+customer[26]+\
                     "\n- BTW afhandeling     \t= "+customer[33]+\
                     "\n- IBAN                \t= "+customer[34]+\
                     "\n- BIC                 \t= "+customer[35]+\
                     "\n- Klantkorting        \t= "+customer[36]+"% (bij partner)"+\
                     "\n- Leververbod         \t= "+customer[37]+\
                     "\n- Kredietlimiet       \t= "+customer[38]+\
                     "\n- OptIn               \t= "+customer[39]+\
                     "\n- Employees           \t= "+customer[40]+\
                     "\n- CustomerGroup_ID\t= "    +customer[41]+\
                     "\n- CustomerSource_ID   \t= "+customer[42]+\
                     "\n- Account_manager   \t= "  +customer[43]+\
                     "\n- Branchecode     \t= "    +customer[44]+\
                     "\n- KvK nummer       \t= "   +coc_nr+\
                     "\n- KvK vestigingsnr\t= "+customer[31]+\
                     btwstring
        comment = self.remove_non_ascii(comment)

        #for easy forwarding
        cust_dict     = {
                        #header
                        'is_company'   : 1,
                        'name'         : name,
                        'street_name'  : street_name,
                        'street_number': street_number,
                        'street2'      : street2,
                        'zip'          : zipcode,
                        'city'         : city,
                        'country_id'   : country_id,
                        'sector_id'    : sector,
                        'phone'        : phone,
                        'mobile'       : mobile,
                        'email'        : email,
                        'website'      : website,
                        'lang'         : lang,
                        'message_is_follower':message_is_follower,
                        #sales & purchases
                        'customer'     : is_customer,
                        'is_ad_agency' : is_ad_agency,
                        'coc_registration_number' : coc_nr,
                        'promille_id'  : tmg_nr, 
                        #financial administration
                        'property_payment_term_id' : property_payment_term_id,
                        'trust'        : trust,
                        'vat'          : btwnr,
                        #notes tab
                        'comment'      : comment
                        }

        #search for promille id
        #note: multiple id's in string field requires removing false positives, i.e. 23 found within 1234
        customers_found = self.env['res.partner'].search([('promille_id', 'like', tmg_nr)])
        verified = []
        if len(customers_found)>0:
            for c in customers_found:
                if (re.match('^' +str(tmg_nr)+'$' , str(c.promille_id))!=None or\
                    re.match('^' +str(tmg_nr)+',' , str(c.promille_id))!=None or\
                    re.match(' ' +str(tmg_nr)+'$' , str(c.promille_id))!=None or\
                    re.match(' ' +str(tmg_nr)+',' , str(c.promille_id))!=None    ) : 
                    verified.append(c)
                  
        if len(verified)==1 : 
            status['c_found'] += 1
            status['last_status']="Klant met TMG klantnr " + tmg_nr + " reeds aangelegd."
            #no informational message here
            return status
        
        if len(verified)>1:
                status['c_error'] += 1
                status['last_status']="Meerdere klanten met TMG klantnr " + tmg_nr + ". Repareer dit!!"
                status['c_messages'] += "- "+status['last_status']+"<br>"
                return status

        """ 
        todo: review coc_nr module, e.g. compute needs depends according documenation
        and search, via custom filter, is giving TypeError: _search_identification() takes exactly 4 arguments (5 given)

        #check on COC_registration number
        _logger.info("coc_nr : " + coc_nr)
        customers_found = self.env['res.partner'].search([('coc_registration_number', '=', coc_nr )])  
        if len(customers_found)==1 : 
            status['c_coc_match'] += 1
            status['last_status']="Klant gevonden met KvK nr " + coc_nr + ". Wordt uitgebreid met nieuwe gegevens."
            status['c_messages'] += "- "+status['last_status']+"<br>"
            self.extend_customer(customers_found[0], cust_dict)
            return status
        #sanity check after removing false positives
        if len(customers_found)>1:
            status['c_error'] += 1
            status['last_status']="Meerdere klanten met KvK nr " + coc_nr + ". Repareer dit!!"
            status['c_messages'] += "- "+status['last_status']+"<br>"
            return status
        """

        #search for email adres, update and return if one found, report warning if multiple found, continue if none found
        if email!="":
            customers_found = self.env['res.partner'].search([('email', '=', email)])
            if len(customers_found)==1:
                status['c_email_match'] += 1
                status['last_status']="Klant met email adres " + email + " gevonden en uitgebreid met Promille gegevens."
                status['c_messages'] += "- "+status['last_status']+"<br>"
                self.extend_customer(customers_found[0], cust_dict)
                return status
            if len(customers_found)>1 :  
                status['c_error'] += 1
                status['last_status']="Meerdere klanten met email adres " + email + ". Repareer dit!!"
                status['c_messages'] += "- "+status['last_status']+"<br>"
                return status

        #prep name for losely search  
        search_name = name.replace("bv","").replace("b.v.","").replace("nv","").replace("n.v.","").replace("vof", "").replace("BV","").replace("B.V.","").replace("NV","").replace("N.V.","")

        #search for name/zip/housenr, update and return if one found, report warning if multiple found, continue if none found
        if search_name!="" and zipcode!="" and street_number!="" :
            customers_found = self.env['res.partner'].search([('name', 'like', search_name),('zip', '=', zipcode),('street', 'like', street_number)])
            verified = []
            if len(customers_found)==1 and (re.match('^' +str(street_number)+'$' ,        str(customers_found[0].street))!=None or\
                                            re.match('^' +str(street_number)+'[a-zA-Z]' , str(customers_found[0].street))!=None or\
                                            re.match(' ' +str(street_number)+'$' ,        str(customers_found[0].street))!=None or\
                                            re.match(' ' +str(street_number)+'[a-zA-Z]' , str(customers_found[0].street))!=None    ) : 
                    verified.append(c)

            if len(verified)==1 : 
                status['c_name_zip_match'] += 1
                status['last_status']="Name + zip + huisnummer gevonden voor : " + search_name + " + " + zipcode + " + " + street_number + ". Bestaande klant wordt uitgebreid."
                status['c_messages'] += "- "+status['last_status']+"<br>"
                self.extend_customer(customers_found[0], cust_dict)
                return status

            if len(verified)>1: 
                status['c_error'] += 1
                status['last_status']="Name + zip + huisnummer combinatie " + name + " + " + zipcode + " + " + street_number +  " komt meerdere keren voor. Repareer dit!!"
                status['c_messages'] += "- "+status['last_status']+"<br>"
                return status

        #search for name/telnr, update and return if one found, report warning if multiple found, continue if none found
        if name!="" and phone!="" :
            customers_found = self.env['res.partner'].search([('name', 'like', search_name),('phone', '=', phone)])
            if len(customers_found)==1 : 
                status['c_name_phone_match'] += 1
                status['last_status']="Naam + telefoon combinatie gevonden voor : " + search_name + " + " + phone + ". Bestaande klant wordt uitgebreid."
                status['c_messages'] += "- "+status['last_status']+"<br>"
                self.extend_customer(customers_found[0], cust_dict)
                return status
            if len(customers_found)>0 : 
                status['c_error'] += 1
                status['last_status']= "Naam en telefoon combinatie komt meerdere keren voor voor: " + name + " + " + phone + ". Repareer dit!!" 
                status['c_messages'] += "- "+status['last_status']+"<br>"
                return status

        #if still not found create it
        status['c_new'] += 1
        status['last_status']="Klant " +  name + " aangemaakt voor promille id "+ tmg_nr
        status['c_messages'] += "- "+status['last_status']+"<br>"
        self.create_customer(cust_dict)
        return status


    def extend_customer(self, customer, cust_dict):
        if customer.promille_id!=False : cust_dict['promille_id'] = customer.promille_id + ", " + cust_dict['promille_id'] 
        if customer.comment    !=False : cust_dict['comment']     = customer.comment + "\nAangevuld\n" + cust_dict['comment']
        update_dict = {
                      'promille_id' : cust_dict['promille_id'],
                      'comment'     : cust_dict['comment']
                      }
        if customer.email==False : update_dict['email']=cust_dict['email']  #else new email found in comment, or already there
        customer.write(update_dict)
        customer._cr.commit()
        return True

    def create_customer(self, cust_dict):
        cust_dict['street']=cust_dict['street_name']+" "+cust_dict['street_number']
        cust_dict.pop('street_name')
        cust_dict.pop('street_number')
        ResPartner = self.env['res.partner']
        ResPartner.create(cust_dict)
        ResPartner._cr.commit()
        return True

""" contacts """

    #def process_contact_files(self, work_dir, files):
    #    return True



"""  orders  """
    #def process_orders(self, work_dir, files):
    #    return True



