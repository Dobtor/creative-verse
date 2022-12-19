# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    customize_default_avatar = fields.Boolean(related="website_id.customize_default_avatar",readonly=False)
    customize_default_section = fields.Boolean(related="website_id.customize_default_section",readonly=False)
    signup_default_avatar = fields.Image(related="website_id.signup_default_avatar",readonly=False)
    signup_default_section = fields.Image(related="website_id.signup_default_section",readonly=False)