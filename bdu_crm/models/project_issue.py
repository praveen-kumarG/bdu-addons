# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, date, timedelta, time

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

    @api.onchange('zip', 'street_number', 'edition_id')
    def onchange_reset_priority(self):
        domain = []
        if self.zip:
            domain +=[('zip','=', self.zip)]
        if self.street_number:
            domain +=[('street_number','=', self.street_number)]
        if domain and self.edition_id:
            self.priority = self.env['issue.priority.rule'].calc_priority(domain, self.edition_id)



class ProjectSolution(models.Model):
    _name = 'project.solution'
    _description = 'Project Solution'

    name = fields.Char(string="Name")
    project_ids = fields.Many2many('project.project', 'project_solution_rel', 'solution_id', 'project_id', string='Projects',)


class IssuePriorityRule(models.Model):
    _name = 'issue.priority.rule'
    _description = 'Project Priority Rule'
    _rec_name = 'days'

    @api.model
    def create(self, vals):
        if len(self.search([])) >= 1:
            raise UserError(_("You can't create more than one rule"))
        return super(IssuePriorityRule, self).create(vals)

    days = fields.Integer('No. Of Days')
    rule_line_ids = fields.One2many('issue.priority.rule.line', 'line_id', 'Rule Line')


    def calc_priority(self, domain, edition):
        priority = '0'
        if not edition or not domain: return priority

        ProIssue = self.env['project.issue']
        slf_obj = self.search([], limit=1)
        if not slf_obj or not slf_obj.rule_line_ids:
            return 0
        tdy_date = datetime.now().date()
        current_date = datetime.combine(tdy_date, time.max).strftime('%Y-%m-%d %H:%M:%S')
        old_date = datetime.combine((tdy_date + timedelta(days=-slf_obj.days)), time.min).strftime('%Y-%m-%d %H:%M:%S')
        domain += [
            ('create_date', '<=', current_date),
            ('create_date', '>=', old_date),
        ]
        issue_objs = ProIssue.search(domain)
        totIssue = len(issue_objs)
        if issue_objs:
            found = issue_objs.search([('edition_id','=',edition.id)], limit=1)
            if found:
                priority = found.priority
            else:
                filterObjs = {}
                for rule_obj in slf_obj.rule_line_ids:
                    if rule_obj.parse_operator(totIssue+1):
                        filterObjs[rule_obj.no_of_issues] = rule_obj
                for key in sorted(filterObjs):
                    priority = filterObjs[key].priority
                    break
        return priority


class IssuePriorityRuleLine(models.Model):
    _name = 'issue.priority.rule.line'
    _description = 'Project Priority Rule Line'
    _rec_name = 'priority'

    line_id = fields.Many2one('issue.priority.rule', 'Rule')
    no_of_issues = fields.Integer('No. Of Issues')
    priority = fields.Selection([('0', 'Low'), ('1', 'Normal'), ('2', 'High')], 'Priority', index=True, default='0')
    operators = fields.Selection([('>', 'Greater Than'), ('<', 'Less Than'), ('==', 'Equal'),('>=', 'Greater & Equal'), ('<=', 'Less & Equal')], 'Operators', index=True)

    _sql_constraints = [('priority_uniq', 'unique(priority)','Rule line priority must be unique per line!'),
        ('no_of_issues_operators_uniq', 'unique(no_of_issues,operators)','Rule line operator & number of issues must be unique per line!'),
    ]

    @api.multi
    def parse_operator(self, value):
        assert len(self.ids) == 1, "you can open only one record at a time"
        if self.operators == '>':
            return value > self.no_of_issues
        elif self.operators == '<':
            return value < self.no_of_issues
        elif self.operators == '>=':
            return value >= self.no_of_issues
        elif self.operators == '<=':
            return value <= self.no_of_issues
        elif self.operators == '==':
            return value == self.no_of_issues

