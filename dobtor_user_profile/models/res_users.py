# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Users(models.Model):
    _inherit = 'res.users'

    profile_section = fields.Image(related='partner_id.profile_section', inherited=True, readonly=False)

    @api.model
    def create(self, vals):
        website = self.env['website'].get_current_website()
        if website.customize_default_avatar:
            vals['image_1920'] = website.signup_default_avatar
        if website.customize_default_section:
            vals['profile_section'] = website.signup_default_section
        return super().create(vals)
 