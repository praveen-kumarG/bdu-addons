# -*- coding: utf-8 -*-
import pdb
from odoo import api, fields, models


class ProductOnlineOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    online_attachment_ids     = fields.Many2many('ir.attachment', string="Attachment(s)")
    online_url_to_material    = fields.Char('URL material')

    online_landing_page       = fields.Char('Landing page')
    online_retarget           = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Retarget')
    online_profile            = fields.Many2many('online.profile', string="Profile")
    online_from_date          = fields.Date('Show from')
    online_to_date            = fields.Date('Show until')
    online_adv_issue_ids      = fields.Many2many('sale.advertising.issue', string='Publiced in')
    online_notes              = fields.Text('Notes') 


    @api.model
    def create(self, vals):
        result = super(ProductOnlineOrderLine, self).create(vals)
        #create always returns draft state, but nevertheless a check
        if result.custom_orderline==u'Online' and result.order_id.state==u'sale' :
            self.update_project_task()
        return result

    @api.multi
    def write(self, vals):
        result = super(ProductOnlineOrderLine, self).write(vals)
        if self.custom_orderline==u'Online' and self.order_id.state ==u'sale' :
            self.update_project_task()
        return result

    @api.multi
    def update_project_task(self) :
        task_name    = self.order_id.name+'-'+str(self.id)
        project_id   = self.env['project.project'].search([('name','=','Online')])
        if not project_id :
            project_id = False
        else :
            project_id = project_id[0]
        current_task = self.env['project.task'].search([('name','=', task_name)])
        profiles = ""
        for profile in self.online_profile :
            if profiles=="" :
                profiles = profile.name
            else : 
                profiles += ', '+profile.name
        websites = ""
        for website in self.online_adv_issue_ids :
            if websites=="" :
                websites = website.name
            else : 
                websites += ', '+website.name
        info = {
                'name'          : task_name,
                'project_id'    : project_id.id,
                'date_deadline' : self.online_from_date,
                'partner_id'    : self.order_id.partner_id.id, 
                'description'   : 'Product  = '+self.product_id.name+'<br/>'+
                                  'Quantity = '+str(self.product_uom_qty)+' x '+str(self.price_unit)+' / '+self.product_uom.name+' = '+str(self.product_uom_qty*self.price_unit)+'<br/>'+
                                  'Url2mat. = '+str(self.online_url_to_material)+'<br/>'+
                                  'Landingp.= '+self.online_landing_page+'<br/>'+
                                  'Retarget = '+self.online_retarget+'<br/>'+
                                  'Profiles = '+profiles+'<br/>'+
                                  'From date= '+self.online_from_date+'<br/>'+
                                  'To date  = '+self.online_to_date+'<br/>'+
                                  'Remarks  = '+self.online_notes+'<br/>'+
                                  'Websites = '+websites+'<br/>'
        }
        stage_ids   = self.env['project.task.type'].search([('project_ids','=',project_id.id)]).sorted(key=lambda r: r.sequence)
        last_stage  = stage_ids[len(stage_ids)-1]
        first_stage = stage_ids[0]
        #if canceled set to last stage
        if self.order_id.state=='cancel' :
            info['stage_id'] = last_stage.id
        if not current_task :
            self.env['project.task'].create(info)
        else :
            #reset if order reset to sale again to first stage, otherwise respect current stage
            if current_task.stage_id.id == last_stage.id and self.order_id.state=='sale' : 
                info['stage_id'] = first_stage.id  
            current_task.write(info)
        return


class ProductOnlineSaleOrder(models.Model):
    _inherit = ["sale.order"]

    @api.multi
    def action_confirm(self):
        result = super(ProductOnlineSaleOrder, self).action_confirm()
        for order_line in self.order_line:
            if order_line.custom_orderline==u'Online' :
                order_line.update_project_task()
        return result


    @api.multi
    def action_cancel(self):
        result = super(ProductOnlineSaleOrder, self).action_cancel()
        for order_line in self.order_line:
            if order_line.custom_orderline==u'Online' :
                order_line.update_project_task()
        return result
