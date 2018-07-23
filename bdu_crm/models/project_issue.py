# -*- coding: utf-8 -*-

from odoo import api, fields, models

class ProjectSource(models.Model):
    _name = 'project.source'
    _description = 'Project Source'
    _rec_name = 'name'

    # @api.multi
    # def name_get(self):
    #     result = []
    #     for source in self:
    #         result.append((source.id, source.name))
    #     return result[:7]

    name = fields.Char('Source')
    project_ids = fields.Many2many('project.project', 'project_source_rel', 'source_id', 'project_id', string='Projects',)

class ProjectIssueType(models.Model):
    _name = 'project.issue.type'
    _description = 'Project Issue Type'
    _rec_name = 'name'

    # @api.multi
    # def name_get(self):
    #     result = []
    #     for issue in self:
    #         result.append((issue.id, issue.name))
    #     return result[:7]

    name = fields.Char('Issue Type')
    project_ids = fields.Many2many('project.project', 'project_issue_type_rel', 'issue_id', 'project_id', string='Projects',)

class ProjectIssue(models.Model):
    _inherit = 'project.issue'

    source = fields.Many2one('project.source', string='Source', copy=False, domain="[('project_ids', '=', project_id)]")
    issue_type = fields.Many2one('project.issue.type', string='Issue Type', copy=False, domain="[('project_ids', '=', project_id)]")
    solution = fields.Html('Solution')
    deadline = fields.Datetime('Deadline')
    title_id = fields.Many2one('sale.advertising.issue', string='Title')
    title_name = fields.Text(related='title_id.default_note', string='Title Name')
    edition_date = fields.Date(string='Edition Date')
    edition_id = fields.Many2one('sale.advertising.issue', string='Edition')
    partner_name = fields.Char(string='Partner Name')
    zip = fields.Char(string='Zip')
    city = fields.Char(string='City')
    street_name = fields.Char(string='Street Name')
    street_number = fields.Char(string='Street Number')
    solution_id = fields.Many2one('project.solution', string="Solution", copy=False, domain="[('project_ids', '=', project_id)]")

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.partner_name = self.partner_id.name
        self.street_number = self.partner_id.street
        self.street_name = self.partner_id.street2
        self.city = self.partner_id.city
        self.zip = self.partner_id.zip
        return super(ProjectIssue, self)._onchange_partner_id()

    @api.onchange('zip', 'street_number')
    def on_change_zip_street_number(self):
        if not self.partner_id:
            postal_code = self.zip and self.zip.replace(' ', '')
            if not (postal_code and self.street_number):
                return {}
            provider_obj = self.env['res.partner'].get_provider_obj()
            if not provider_obj:
                return {}
            pc_info = provider_obj.getaddress(postal_code, self.street_number)
            if not pc_info or not pc_info._data:
                return {}
            self.street_name = pc_info.street
            self.city = pc_info.town

    @api.onchange('title_id', 'edition_date')
    def onchange_title_id(self):
        self.edition_id = False

class ProjectSolution(models.Model):
    _name = 'project.solution'

    name = fields.Char(string="Name")
    project_ids = fields.Many2many('project.project', 'project_solution_rel', 'solution_id', 'project_id', string='Projects',)
