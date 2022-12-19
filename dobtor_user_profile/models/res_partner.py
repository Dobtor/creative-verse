# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.http import request
from odoo.tools.translate import html_translate


class Partner(models.Model):
    _inherit = 'res.partner'

    profile_section = fields.Image(string='Profile Section')
    profile_description = fields.Text(string='Description for User Profile', translate=True)
    profile_content = fields.Html(string="Content for user profile", translate=html_translate)
    

    @api.model
    def get_partner_edit_data(self):
        partner = request.env.user.partner_id
        res = partner.read([
            'id', 'name', 'street', 'profile_description',
        ])[0]

        return res

    def _translate_val_list(self):
        res = super()._translate_val_list()
        list = {
            'nickname': _('Nickname'),
        }
        res.update(list)
        
        return res