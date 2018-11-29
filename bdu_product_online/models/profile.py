# -*- coding: utf-8 -*-
from odoo import models, fields, api

class SearchProfile(models.Model):
	_name        = 'online.profile'
	_description = 'search profiles for programmatic selling'
	
	profile_cat  = fields.Char('Profile category')
	name         = fields.Char('Profile',                 required=True)
	color        = fields.Integer('Color index')
	remark       = fields.Char('Remark')

"""
Color index	Tags odoo 10

	0	grey
	1	green
	2	yellow
	3	orange
	4	red
	5	purple
	6	blue
	7	cyan
	8	light green
	9	magenta
	
"""