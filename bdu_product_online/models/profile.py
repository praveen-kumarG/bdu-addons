# -*- coding: utf-8 -*-
from odoo import models, fields, api

class SearchProfile(models.Model):
	_name        = 'online.profile'
	_description = 'search profiles for programmatic selling'
	
	profile_cat  = fields.Char('Profile category',        required=False)
	name         = fields.Char('Profile',                 required=True)