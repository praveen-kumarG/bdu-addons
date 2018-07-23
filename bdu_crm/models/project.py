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