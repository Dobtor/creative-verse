# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class EventTagCategory(models.Model):
    _inherit = 'event.tag.category'

    mode = fields.Selection(
        selection_add=[("demand", _("Demand"))],
        ondelete={'demand': lambda r: r.write({'mode': 'demand'})}
    )