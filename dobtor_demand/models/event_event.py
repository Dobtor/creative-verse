# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.addons.http_routing.models.ir_http import slug


class EventType(models.Model):
    _inherit = 'event.type'

    mode = fields.Selection(
        selection_add=[("demand", _("Demand"))],
        ondelete={'demand': lambda r: r.write({'mode': 'demand'})}
    )

class EventEvent(models.Model):
    _inherit = 'event.event'

    mode = fields.Selection(
        selection_add=[("demand", _("Demand"))],
        ondelete={'demand': lambda r: r.write({'mode': 'demand'})}
    )
    demand_type = fields.Selection(
        string='Demand Type',
        selection=[
            ('taker', _('Taker')),
            ('giver', _('Giver'))
        ],
        default="taker"
    )
    demand_ids = fields.One2many(
        string='Demand',
        comodel_name='event.demand',
        inverse_name='event_id'
    )

    @api.depends('name')
    def _compute_website_url(self):
        super()._compute_website_url()
        for demand in self.filtered(lambda e:e.mode == 'demand'):
            if demand.id:  
                demand.website_url = '/demand/%s' % slug(demand)