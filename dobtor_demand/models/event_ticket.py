# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class EventEventTicket(models.Model):
    _inherit = 'event.event.ticket'

    pricing_method = fields.Selection(
        string="Pricing Method",
        selection=[
            ('times', _('Times')),
            ('per_min', _('per min')),
            ('per_hour', _('per hour')),
        ],
        default='times'
    )
    demand_type = fields.Selection(
        string='Demand Type',
        related='event_id.demand_type',
        readonly=True
    )

    min_request_unit = fields.Integer(
        string='Min Request Unit',
        default=1,
    )
    # 需求數
    request_qty = fields.Integer(
        string='Request Qty',
        default=1,
    )
    # 已完成
    request_reserved = fields.Integer(
        string='Reserved Qty',
        compute='_compute_request',
        store=True
    )
    # 計畫支付
    request_total_amount = fields.Float(
        string='Request Total Amount',
        compute='_compute_request',
        store=True
    )
    # 實際
    reserved_total_amount = fields.Float(
        string='Reserved Total Amount',
        compute='_compute_request',
        store=True
    )

    def _get_ticket_multiline_purchase_description(self):
        self.ensure_one()
        if self.product_id.description_purchase:
            return f'{self.product_id.description_purchase}\n{self.event_id.display_name}'
        return f'{self.display_name,}\n{self.event_id.display_name}'

    def compute_request_constraint(self):
        return """ SELECT event_ticket_id, sum(request_qty) r_qty
                    FROM event_registration
                    WHERE event_ticket_id IN %s AND state in ('open', 'done')
                    GROUP BY event_ticket_id
                """ 

    @api.depends('registration_ids.state', 'price')
    def _compute_request(self):
        for ticket in self:
            ticket.request_reserved = ticket.request_total_amount = 0
        if self.ids:                   
            self.env['event.registration'].flush(['event_id', 'event_ticket_id' ,'state', 'request_qty'])
            self.env.cr.execute(self.compute_request_constraint(), (tuple(self.ids),))
            for event_ticket_id, r_qty in self.env.cr.fetchall():
                ticket = self.browse(event_ticket_id)
                ticket.request_reserved += r_qty
        for ticket in self:
            ticket.reserved_total_amount = ticket.request_reserved * ticket.price
            ticket.request_total_amount = ticket.request_qty * ticket.price
