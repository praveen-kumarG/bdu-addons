# -*- coding: utf-8 -*-

from odoo import api, fields, models

class ProjectSource(models.Model):
    _name = 'project.source'
    _description = 'Project Source'
    _rec_name = 'name'

    @api.multi
    def name_get(self):
        result = []
        for source in self:
            result.append((source.id, source.name))
        return result[:7]

    name = fields.Char('Source')

class ProjectIssueType(models.Model):
    _name = 'project.issue.type'
    _description = 'Project Issue Type'
    _rec_name = 'name'

    @api.multi
    def name_get(self):
        result = []
        for issue in self:
            result.append((issue.id, issue.name))
        return result[:7]

    name = fields.Char('Issue Type')


class ProjectIssue(models.Model):
    _inherit = 'project.issue'

    source = fields.Many2one('project.source', 'Source')
    issue_type = fields.Many2one('project.issue.type', 'Issue Type')
    solution = fields.Html('Solution')
    deadline = fields.Datetime('Deadline')