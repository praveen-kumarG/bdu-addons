# -*- coding: utf-8 -*-
import datetime, pdb
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PubbleProductionData(models.Model):
    _name               = 'pubble.production.data'
    _description        = 'Collected Pubble production data'

    #unique reference and name in one
    name                = fields.Char('Pubble reference') 

    #billing line belongs to one article with article attributes
    article_id          = fields.Integer('Article')
    product_id          = fields.Many2one('product.product',              string='Product')
    count               = fields.Integer('Count')
    unit_price          = fields.Float('Unit price')
    total_price         = fields.Float('Total')
    pubble_product      = fields.Char('Pubble product')
    pubble_count        = fields.Integer('Pubble count')
    freelancer          = fields.Many2one('res.partner',                  string='Freelancer')
    url                 = fields.Char('Url')
    remark              = fields.Char('Werktitel')

    #first issue (hence ou) reported takes the costs, other publications administered for reference
    title               = fields.Char('Title')
    issue_id            = fields.Many2one('sale.advertising.issue',       string='Issue')
    analytic_account_id = fields.Many2one('account.analytic.account',     string='Analytic account', 
                                                                          store=True)
    operating_unit_id   = fields.Many2one('operating.unit',               string='Operating Unit')
    titles              = fields.Char('Title')
    publications        = fields.Char('Publications')
    related_costs       = fields.Char('Related costs')
  
    #time stamp : first issue has preference over time of acceptance, locked after processed
    issue_date          = fields.Date('Issue date')
    year                = fields.Integer('Year')
    week                = fields.Integer('Week')

    #empty, one or more
    commissioned_by     = fields.Char('Commissioned by')
    commissioned_by_xxl = fields.Char('Commissioned by') 
    #status fields
    accepted            = fields.Boolean('OK')
    processed           = fields.Boolean('Processed')
    message             = fields.Char('Info')
    

    #works only on the field at client side, not the button changing it
    @api.onchange('accepted')
    def onchange_accepted(self) :
        if self.accepted and not self.freelancer :
            raise ValidationError("No freelancer to pay. Add freelancer first before accepting.")
            self.accepted = False
            return 
        if self.accepted and not self.operating_unit_id :
            raise ValidationError("No operating unit. Check advertising issue.")
            self.accepted = False
            return 
        if self.accepted and not self.product_id :
            raise ValidationError("No product. Check product conversion.")
            self.accepted = False
            return 
        if self.accepted and not self.issue_id :
            raise ValidationError("No issue. Check Pubble title code and date, as well as advertising issue.")
            self.accepted = False
            return 
        if not self.accepted :
            return 
        if self.accepted and self.freelancer :
            if not self.issue_date :
                self.year=str(datetime.date.today().isocalendar()[0])
                self.week=str(datetime.date.today().isocalendar()[1])
        return 

    @api.multi
    def accept(self) :
        self.accepted = not self.accepted
        #button is not triggering client side onchange
        self.onchange_accepted()
        return

    @api.multi
    def push_to_sow(self) :
        pdb.set_trace()
        selection=self.env['pubble.production.data'].browse(self.env.context.get('active_ids'))
        already_processed     = 0
        not_accepted          = 0
        not_operating_unit_id = 0
        not_freelancer        = 0
        not_product_id        = 0
        not_issue_id          = 0
        not_product_categ     = 0
        not_product_expense_account = 0

        #check first
        for line in selection :
            if line.processed :
                already_processed += 1
            if not line.accepted :
                not_accepted += 1
            if not line.operating_unit_id :
                not_operating_unit_id += 1
            if not line.freelancer :
                not_freelancer += 1
            if not line.product_id :
                not_product_id += 1
            if not line.issue_id :
                not_issue_id += 1
            if not line.product_id.categ_id :
                not_product_categ += 1
            if not line.product_id.property_account_expense_id :
                not_product_expense_account += 1
        
        if (already_processed + not_accepted + not_operating_unit_id + not_freelancer + not_product_id + not_issue_id + not_product_categ + not_product_expense_account) > 0 :
            message = "Your selection can not be processed !\n"
            if already_processed > 0 :
                message += str(already_processed)+" already processed records\n"
            if not_accepted>0 :
                message += str(not_accepted)+" records that are not accepted\n"
            if not_operating_unit_id>0 :
                message += str(not_operating_unit_id)+" records without operating unit (check advertising issue definitions)\n"
            if not_freelancer > 0 :
                message += str(not_freelancer)+" records with a missing freelancer\n"
            if not_product_id > 0 :
                message += str(not_product_id)+" records have missing product (check pubble product conversion definitions)\n"
            if not_issue_id > 0 :
                message += str(not_issue_id)+" records have missing issue (check advertising issue definitions)\n"
            if not_product_categ > 0 :
                message += str(not_product_categ)+" records have missing product category on product (check product for missing product category)\n"
            if not_product_expense_account > 0 :
                message += str(not_product_expense_account)+" records have products with missing expense account (check product for missing expense account)\n"
            raise ValidationError(message)
            return False
        
        #al ok, then we process per OU (can be different company, depending on user's authorizations)
        operating_units=selection.read_group([('operating_unit_id','!=',False)],{'operating_unit_id'},{'operating_unit_id'})
        for operating_unit in operating_units :
            
            ou_id = operating_unit['operating_unit_id'][0]
            ou    = self.env['operating.unit'].browse(ou_id)
            c_id  = ou.company_id.id
            ou_selection = selection.search([('operating_unit_id','=', ou_id)])
            
            #create batch            
            batch={}
            batch['name']       = "Freelancers_redactie_"+ou.name
            batch['name']      += "_"+str( (datetime.datetime.today()-timedelta(weeks=1)).isocalendar()[0])
            batch['name']      += "_"+str( (datetime.datetime.today()-timedelta(weeks=1)).isocalendar()[1])
            batch['date_batch'] = datetime.datetime.today().strftime("%Y-%m-%d")
            batch['company_id'] = c_id
            batch['comment']    = "Pushed from Pubble admittance"
            batch_rec = self.env['sow.batch'].create(batch)

            #sow_lines
            for line in ou_selection :
                sow_line={}
                sow_line['batch_id']           = batch_rec.id
                sow_line['name']               = line.remark
                sow_line['issue_id']           = line.issue_id.id
                sow_line['partner_id']         = line.freelancer.id
                sow_line['employee']           = False
                sow_line['product_category_id']= line.product_id.categ_id.id
                sow_line['product_id']         = line.product_id.id
                sow_line['account_id']         = line.product_id.property_account_expense_id.id
                sow_line['quantity']           = line.count
                #not used
                sow_line['page']               = 0
                sow_line['nr_of_columns']      = 0
                #save and force price update
                revbil_sow_rec = self.env['revbil.statement.of.work'].create(sow_line)
                revbil_sow_rec._onchange_calculatePrice()   
                
                #mark line done to prevent duplicate invoicing
                line.write({'processed':True})
        return


    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True) :
        #do not sum year and week fields
        if 'year' in fields :
            fields.remove('year')
        if 'week' in fields :
            fields.remove('week')
        if 'article_id' in fields and 'article_id' not in groupby :
            fields.remove('article_id')
        return super(PubbleProductionData, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
