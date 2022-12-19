# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _


class Website(models.Model):
    _inherit = "website"

    customize_default_avatar = fields.Boolean(string='Default Avatar', default=False)
    customize_default_section = fields.Boolean(string='Default Section', default=False)
    signup_default_avatar = fields.Image(string='Signup Default Avatar', max_width=1920, max_height=1920)
    signup_default_section = fields.Image(string='Signup Default Section')