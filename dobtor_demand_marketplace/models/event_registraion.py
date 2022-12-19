# -*- coding: utf-8 -*-
import logging
from multiprocessing import set_forkserver_preload
from odoo import models, fields, api, _
_logger = logging.getLogger(__name__)


class EventRegistration(models.Model):
    _inherit = 'event.registration'

    demand_so_id = fields.Many2one(
        'sale.order', 
        string='Demand Sale Order', 
        ondelete='set null', 
        copy=False
    )
    demand_so_line_id = fields.Many2one(
        'sale.order.line',
        string='Demand Sale Order Line',
        ondelete='set null', 
        copy=False
    )
    demand_type = fields.Selection(
        string='Demand Type',
        related='event_id.demand_type',
        readonly=True
    )
    # region : After demand finish/Check
    is_creator_check = fields.Boolean(
        string='Creator Check',
        default=False
    )
    is_attendee_finish = fields.Boolean(
        string='Attendee Finish',
        default=False
    )
    appeal_state = fields.Selection(
        string='appeal state',                        # 申訴狀態
        selection=[
            ('no_one', _('No one appeal')),          # 無人申訴
            ('creator', _('Create appeal')),         # 活動創建者 申訴
            ('attendee', _('Attendee appeal')),      # 申訴
            ('both', _('Both appeal')),              # 兩者都有申訴
        ],
        default="no_one"
    )
    # endregion

    # region : before demand
    organizer_state = fields.Selection(
        string='organizer state',       # 群組 在Taker/Giver 來報名前的審核狀態
        selection=[
            ('draft', _('Pending')),    # 群組 看到 attendee 的申請 (待審核)
            ('open', _('Confirm')),     # 群組 同意
            ('cancel', _('Reject')),    # 群組 拒絕
        ],
        default="draft"
    )
    demand_creator_state = fields.Selection(
        string='demand creator state',           
        selection=[
            ('draft', _('Pending')),    # demand creator 看到 attendee 的申請 (待審核)
            ('open', _('confirm')),     # demand creator 同意
            ('cancel', _('Reject')),    # demand creator 拒絕
        ],
        default="draft"
    )
    # endregion

    def action_set_draft(self):
        super().action_set_draft()
        self.write({
            'organizer_state': 'draft',
            'demand_creator_state' : 'draft',
            'appeal_state': 'no_one',
            'is_creator_check' : False,
            'is_attendee_finish': False
        })

    def action_creator_appeal(self):
        for res in self:
            if res.appeal_state == 'no_one':
                res.appeal_state = 'creator'
            else:
                res.appeal_state = 'both'

    def action_attendee_appeal(self):
        for res in self:
            if res.appeal_state == 'no_one':
                res.appeal_state = 'attendee'
            else:
                res.appeal_state = 'both'

    def creator_appeal(self, post={}):
        self.action_creator_appeal()

    def creator_check(self, post={}):
        self.action_creator_check()

    def attendee_appeal(self, post={}):
        self.action_attendee_appeal()

    def attendee_finish(self, post={}):
        self.action_attendee_finish()

    def action_creator_check(self):
        for res in self:
            res.is_creator_check = not res.is_creator_check
            if res.is_creator_check:
                subject = 'Demand Is Finished'
                body = 'Thank you for you help!!'
                email_to = res.event_id.event_creator_partner.email 
                if email_to:
                    res._sent_state_mail(subject, body, email_to)
            if res.is_creator_check and res.is_attendee_finish and res.state != 'cancel':
                res.action_settle()

    def action_attendee_finish(self):
        for res in self:
            res.is_attendee_finish = not res.is_attendee_finish
            if res.is_attendee_finish:
                subject = f'Demand Finish via {res.partner_id.name}'
                body = f'I am Finish this demand {res.event_id.name} !!'
                email_to = res.partner_id.email
                if email_to:
                    res._sent_state_mail(subject, body, email_to)
            if res.is_creator_check and res.is_attendee_finish and res.state != 'cancel':
                res.action_settle()

    def notify_attendee_join(self):
        '''
            target : Attendee 初次申請 Creator 寄的通知信件.
        '''
        subject = f'Your Join {self.event_id.name} apply'
        body = _('Your Join this Demand, Please wait for agree.')
        email_to = self.event_id.event_creator_partner.email
        if email_to:
            self._sent_state_mail(subject, body, email_to)
    
    def set_demand_creator_state_open(self):
        '''
            target : Creator 同意 Attendee 的通知信
        '''
        self.demand_creator_state = 'open'
        subject = f'{self.event_id.name} agree your apply'
        body = _('Thank you ! Anticipate with your cooperation!')
        email_to = self.event_id.event_creator_partner.email 
        if email_to:
            self._sent_state_mail(subject, body, email_to)
    
    def set_demand_creator_state_cancel(self):
        '''
            target : Creator 拒絕 Attendee 的通知信
        '''
        self.action_cancel()
        self.demand_creator_state = 'cancel'
        subject = f'Cancel your {self.event_id.name} apply'
        body = _('Thank you for this apply, but I may have to say no this time.')
        email_to = self.event_id.event_creator_partner.email 
        if email_to:
            self._sent_state_mail(subject, body, email_to)


    def notify_demand_attendee(self):
        '''
           target : 組織同意後 同時發送信件給 Attendee
        '''
        notify = _('Manager agree this case.') + f' [{self.event_id.name}]'
        email_to = self.event_id.event_creator_partner.email
        if email_to:
            self._sent_state_mail(notify, notify, email_to)

    def notify_demand_creater(self):
        '''
           target : 組織同意後 同時發送信件給 Demand 創建者. 
        '''
        subject = f'{self.partner_id.name} {_("join your demand")}'
        section = _('i can help your.') if self.demand_type == 'taker' else _('i need your help.')
        body = f'How are you? I am {self.partner_id.name} and {section}'
        email_to = self.partner_id.email
        if email_to:
            self._sent_state_mail(subject, body, email_to)

    def set_organizer_state_draft(self):
        '''
            target : 如果是 demand Attendee, 在 Create 時會通知組織.
        '''
        subject = f'{self.partner_id.name} {_("join")} {self.event_id.name}'
        body = f'{self.partner_id.name} {_("join")} {self.event_id.name} , {_("need your agree.")}'
        email_to = self.partner_id.email
        if email_to:
            self._sent_state_mail(subject, body, email_to)

    def set_organizer_state_open(self):
        '''
            target : 組織同意後 同時發送信件給 Giver 和 Taker.
        '''
        self.organizer_state = 'open'
        subject = self.partner_id.name + (_(" can help your.") if self.demand_type == 'taker' else _(' need your help.'))
        body = _('Manager agree this case.') + f' [{self.event_id.name}]'
        # 同時寄給 Giver 和 Taker
        self.notify_demand_attendee()  # for attendee mail
        self.notify_demand_creater()   # for create event partner mail
    
    def website_set_origin_state_open(self, post={}): 
        self.set_organizer_state_open()

    def website_set_origin_state_cancel(self, post={}):
        self.set_organizer_state_cancel()

    def website_set_demand_creator_state_open(self, post={}):
        self.set_demand_creator_state_open()

    def website_set_demand_creator_state_cancel(self, post={}):
        self.set_demand_creator_state_cancel()

    def set_organizer_state_cancel(self):
        '''
            target : 組織拒絕後, 寄信給 Attendee
        '''
        self.action_cancel()
        self.organizer_state = 'cancel'
        subject = f'System Cancel your {self.event_id.name} apply'
        body = _('Thank you for this apply, but I may have to say no this time.')
        email_to = self.event_id.organizer_id.leader_id.email or self.env.company.partner_id.email
        if email_to:
            self._sent_state_mail(subject, body, email_to)


    @api.model_create_multi
    def create(self, vals_list):
        registrations = super().create(vals_list)
        for attendee in registrations:
            if attendee.mode == 'demand':
                attendee.set_organizer_state_draft()
                attendee.notify_attendee_join()
        return registrations

    def _sent_state_mail(self, subject, body, email_to):
        if isinstance(self.id, models.NewId) and self._origin.id:
            self = self._origin
        for record in self:
            template = self.env.ref('dobtor_demand_marketplace.demand_attendee_state_common_mail', raise_if_not_found=False)
            if self._context.get('force_sent_mail',True) and template and self.env.company.email:
                email_values = {
                    'email_to': email_to, 
                    'email_from': self.env.company.email,
                    'subject': subject
                }
                template.sudo().with_context(body=body).send_mail(self.id, email_values=email_values, force_send=True, raise_exception=False)

    def action_settle(self):
        if self.mode == 'demand':
            po = self.demand_po_id
            if len(po):
                po.button_confirm()
                po.demand_action_create_purchase_transaction()
                demand = self.env['event.demand'].sudo().search([('event_id', '=', self.event_id.id)], limit=1)
                if demand.is_team:
                    partner_id = self.event_id.organizer_id.id
                else:
                    if demand.is_use_team_wallet:
                        partner_id = self.event_id.organizer_id.id
                    else:
                        partner_id = self.event_id.event_creator_partner.id
                    
                so = self.env['sale.order'].sudo()
                so_id = so.create({'partner_id': partner_id })
                so_line = so_id.order_line.create({
                    'name': self.event_ticket_id.name,
                    'product_uom_qty':1,
                    'order_id':so_id.id,
                    'request_qty': self.request_qty,
                    'price_unit': self.event_ticket_id.price,
                    'product_id': self.event_ticket_id.product_id.id,
                    'event_id': self.event_id.id,
                    'event_ticket_id': self.event_ticket_id.id
                })
                so_line.product_id_change()
                so_line.event_id = False
                so_line.event_ticket_id = False
                if so_line:
                    # region : 每次交易, 則歸還部分的預扣款
                    if demand.demand_taker_order_id.wallet_txn_id:
                        tx = self.env['payment.transaction'].sudo()
                        acquirer = self.env["payment.acquirer"].sudo().get_gift_acquirer()
                        vals = tx.prepare_wallet_tx_val(acquirer, so_id.amount_total, partner_id, 0, None, "System Compute")
                        tx = tx.create(vals)
                        demand.demand_taker_order_id.wallet_txn_id.write({
                            'child_ids' : [(4, tx.id)]
                        })
                    # endreiong
                    self.demand_so_id = so_id.id
                    self.demand_so_line_id = so_line.id
                    so_id.action_wallet_pay()
                    so_id.action_confirm()
                    so_id.set_agent_payment()
                    so_id.action_generate_and_pay_wallet_invoice()
