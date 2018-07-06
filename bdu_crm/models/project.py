# -*- coding: utf-8 -*-

from odoo import api, fields, models

class ProjectTaksType(models.Model):
    _name = 'task.type'
    _description = 'Task Type'
    _rec_name = 'name'

    name = fields.Char('Task Type')

class Task(models.Model):
    _inherit = 'project.task'

    task_type = fields.Many2one('task.type', 'Task Type')
    date_deadline = fields.Datetime(string='Deadline', index=True, copy=False)

class Project(models.Model):
    _inherit = 'project.project'

    solution_ids = fields.Many2many('project.source', 'project_solution_rel', 'project_id', 'solution_id', string='Project Solutions')
    source_ids = fields.Many2many('project.source', 'project_source_rel', 'project_id', 'source_id', string='Project Sources')
    issue_type_ids = fields.Many2many('project.issue.type', 'project_issue_type_rel', 'project_id', 'issue_id', string='Project Issue Types')