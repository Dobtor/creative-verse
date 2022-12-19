# -*- coding: utf-8 -*-
import pprint
from odoo import SUPERUSER_ID, models, fields, api, _
from odoo.http import request
import logging
_logger = logging.getLogger(__name__)


class EventDemand(models.Model):
    _inherit = 'event.demand'

    demand_giver_order_id = fields.Many2one(
        'purchase.order', 
        string='Giver DownPay Order', 
        ondelete='set null',
        copy=False
    )
    demand_taker_order_id = fields.Many2one(
        'sale.order', 
        string='Taker DownPay Order', 
        ondelete='set null', 
        copy=False
    )
    is_team = fields.Boolean(
        string='Is Team',
        default=False
    )
    is_use_team_wallet = fields.Boolean(
        string='Is Use Team Wallet',
        default=False
    )
    

    def _prepare_sale_order_values(self, partner, pricelist):
        self.ensure_one()
        values = {
            'partner_id': partner.id,
            'pricelist_id': pricelist.id,
        }
        return values

    def computer_downpay(self):
        '''
            用戶提交需求需要預扣時間點數
        '''
        sale_order = self.env['sale.order'].sudo()
        for demand in self:
            so_lines = []

            event_ticket_id = demand.event_ticket_ids[0]
            if event_ticket_id:
                so_line_vals = {
                    'product_id': event_ticket_id.product_id.id,
                    'product_uom_qty': 1,
                    'request_qty': event_ticket_id.request_qty,
                    'name': event_ticket_id.name,
                    'price_unit': event_ticket_id.price,
                    'event_id': demand.event_id.id,
                    'event_ticket_id': event_ticket_id.id
                }
                if len(demand.demand_taker_order_id) > 0 and demand.demand_taker_order_id.state == 'draft':
                    demand.demand_taker_order_id.sudo().order_line.unlink()
                    so_line_vals.update({'order_id':demand.demand_taker_order_id.id })
                    demand.demand_taker_order_id.sudo().order_line.create(so_line_vals)
                    demand.demand_taker_order_id.sudo().order_line.product_id_change()
                else:
                    partner_pl = demand.event_creator_partner.property_product_pricelist
                    pricelist = self.env['product.pricelist'].browse(partner_pl.id).sudo()
                    so_data = self._prepare_sale_order_values(demand.event_creator_partner, pricelist)
                    so_lines.append((0, 0, so_line_vals))
                    sale_order = sale_order.create(so_data)
                    sale_order.write({"order_line": so_lines})
                    demand.demand_taker_order_id = sale_order
                    demand.demand_taker_order_id.order_line.product_id_change()
            return demand.demand_taker_order_id

    def set_state_cancel(self, post={}):
        self._set_state_cancel()

    def set_state_open(self, post={}):
        self._set_state_open()


    def _set_state_cancel_extend(self):
        if self.demand_taker_order_id:
            self.demand_taker_order_id.sudo().action_cancel()
        return super()._set_state_cancel_extend()
    
    def _set_state_closed_extend(self):
        if self.demand_taker_order_id:
            self.demand_taker_order_id.sudo().action_cancel()
        return {}

    def _set_state_give_up_extend(self):
        if self.demand_taker_order_id:
            self.demand_taker_order_id.sudo().action_cancel()
        return super()._set_state_give_up_extend()

    def action_computer_downpay(self):
        return {
            "name": _('Taker DownPay Order'),
            "view_mode": "tree,form",
            "res_model": "sale.order",
            "view_id": False,
            "type": "ir.actions.act_window",
            "context": self.env.context,
            "domain": [("id", "=", self.computer_downpay().id)],
        }

    def _get_email_to(self):
        return self.organizer_id.leader_id.email or self.env.company.partner_id.email

    def actoin_finish_all(self):
        for demand in self:
            for attendee in demand.event_id.registration_ids.filtered(lambda x: x.payment_status in ('to_pay') and x.state != 'cancel' and x.demand_creator_state == 'open' and x.appeal_state == 'no_one'):
                if not attendee.is_creator_check:
                    attendee.action_creator_check()
                if not attendee.is_attendee_finish:
                    attendee.action_attendee_finish()
            if demand.state == 'open':
                demand._set_state_closed()
            if demand.state == 'draft':
                demand._set_state_give_up()

    def _cron_process_demand_finish(self):
        demands = self.env['event.demand'].search([
            ('date_end', '<', fields.Datetime.now()),
            ('demand_type', '=', 'taker'),
            ('is_finished', '=', False)])
        # TODO : is_finiished 作用逐漸式微, 所以之後可以利用 demand.state 來取代. (過渡期間先以 is_finished)
        demands.actoin_finish_all()         
        demands.write({'is_finished': True})

    def demand_edit_fields(self):
        return [
            'name', 'subtitle', 'organizer_id', 'tag_ids', 'date_begin', 'date_end',
            'is_show_public', 'event_ticket_ids', 'description', 'event_address_disabled',

            # region: online address
            'online_address', 'event_address',
            # endregion

            # region: offline address
            'offline_address', 'state_id', 'city', 'zip', 'street',
            # endregion
        ]

    def get_demand_edit_data(self):
        self.ensure_one()
        partner = request.env.user.partner_id
        
        if self.event_creator_partner.id == partner.id:
            res = self.read(self.demand_edit_fields())[0]

            if res['organizer_id']: 
                res['organizer_id'] = [{'id': res['organizer_id'][0], 'text': res['organizer_id'][1]}]
            if res['tag_ids']:
                res['tag_ids'] = request.env['event.tag'].search_read([('id', 'in', res['tag_ids'])], ['name'])
                for tag in res['tag_ids']:
                    tag['text'] = tag.pop('name')
            if res['offline_address']:
                # (id, 'state_name')
                if res['state_id']:
                    # {'id': id, 'name': 'state_name'}
                    offline_state = request.env['res.country.state'].search_read([('id', '=', res['state_id'][0])], ['name'])[0]
                    # {'id': id, 'text': 'state_name'}
                    offline_state['text'] = offline_state.pop('name')
                    res['state_id'] = [offline_state]
            if res['event_ticket_ids']:
                res['event_ticket_ids'] = request.env['event.event.ticket'].search_read(
                    [('id', '=', res['event_ticket_ids'][0])], 
                    ['price', 'pricing_method', 'min_request_unit', 'request_qty']
                )

            return res
