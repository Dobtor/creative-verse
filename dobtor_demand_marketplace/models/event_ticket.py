# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class EventEventTicket(models.Model):
    _inherit = 'event.event.ticket'
    # 申請數
    apply_request_qty = fields.Integer(
        string='Apply request qty',
        compute='_compute_request_qty',
        store=True
    )
    # 已接受
    organizer_confirm_request_qty = fields.Integer(
        string='Not yet request qty',
        compute='_compute_request_qty',
        store=True
    )

    # 未完成
    not_yet_request_qty = fields.Integer(
        string='Not yet request qty',
        compute='_compute_request_qty',
        store=True
    )
    # 待審核
    audit_request_qty = fields.Integer(
        string='Audit request qty',
        compute='_compute_request_qty',
        store=True
    )

    def compute_state_request_qty(self, where_clause=' '):
        return """ SELECT event_ticket_id, sum(request_qty) r_qty
                    FROM event_registration
                    WHERE event_ticket_id IN %s """ \
                    + where_clause + \
                    "GROUP BY event_ticket_id"

    @api.depends('registration_ids.organizer_state', 'registration_ids.demand_creator_state', 'registration_ids.is_creator_check', 'registration_ids.is_attendee_finish', 'price')
    def _compute_request_qty(self):
        for ticket in self:
            ticket.apply_request_qty = ticket.not_yet_request_qty = ticket.organizer_confirm_request_qty = ticket.audit_request_qty = 0
        if self.ids:                   
            self.env['event.registration'].flush(['event_id', 'event_ticket_id' ,'state', 'request_qty', 'organizer_state', 'demand_creator_state'])
            # 申請數
            where_params = [tuple(self.ids)]
            self.env.cr.execute(self.compute_state_request_qty(), where_params)
            for event_ticket_id, r_qty in self.env.cr.fetchall():
                ticket = self.browse(event_ticket_id)
                ticket.apply_request_qty += r_qty
            # 已接受
            where_clause_by_organizer = 'AND organizer_state IN %s '
            where_params = [tuple(self.ids), ('open',)]
            self.env.cr.execute(self.compute_state_request_qty(where_clause_by_organizer), where_params)
            for event_ticket_id, r_qty in self.env.cr.fetchall():
                ticket = self.browse(event_ticket_id)
                ticket.organizer_confirm_request_qty += r_qty
            # 未完成
            where_clause = "AND demand_creator_state IN %s AND (is_creator_check = 'f' OR is_attendee_finish = 'f')"
            where_params = [tuple(self.ids), ('open',)]
            self.env.cr.execute(self.compute_state_request_qty(where_clause), where_params)
            for event_ticket_id, r_qty in self.env.cr.fetchall():
                ticket = self.browse(event_ticket_id)
                ticket.not_yet_request_qty += r_qty
            # 待審核
            where_clause = "AND demand_creator_state IN %s AND organizer_state = 'open' "
            where_params = [tuple(self.ids), ('draft',)]
            self.env.cr.execute(self.compute_state_request_qty(where_clause), where_params)
            for event_ticket_id, r_qty in self.env.cr.fetchall():
                ticket = self.browse(event_ticket_id)
                ticket.audit_request_qty += r_qty