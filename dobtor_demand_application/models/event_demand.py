# -*- coding: utf-8 -*-
from odoo import models, _, api

class EventDemand(models.Model):
    _inherit = 'event.demand'

    # region : Demand Apply Action (apply/open/cancel)
    def set_state_cancel(self, post={}):
        Application = self.env['request.application'].sudo()
        action =  self.env.ref('dobtor_demand_application.action_demand_reject')
        if action.active:
            application = Application.create({
                'res_id': self.id,
                'action_id':action.id,
                'note':post.get('note',False),
                'send_mail_partner_id': self.event_creator_partner.id,
                'partner_id': self.event_creator_partner.id,
                'related_partner_ids': self.organizer_id.id,
                'auditor': self.env.user.id,
                'state': 'cancel',
            })
            if action.auto_confirm:
                application.action_do('reject')
                application.application_cancel_notify()
        else:
            self._set_state_cancel()

    def set_state_open(self, post={}):
        Application = self.env['request.application'].sudo()
        action =  self.env.ref('dobtor_demand_application.action_demand_reject')
        if action.active:
            application = Application.create({
                'res_id': self.id,
                'action_id':action.id,
                'note': action.text_template,
                'send_mail_partner_id': self.event_creator_partner.id,
                'partner_id': self.event_creator_partner.id,
                'related_partner_ids': self.organizer_id.id,
                'auditor': self.env.user.id,
                'state': 'confirm',
            })
            if action.auto_confirm:
                application.action_do()
                application.application_confirm_notify()
        else:
            self._set_state_open()

    def action_demand_reject_application(self):
        self.with_context(force_sent_mail=False)._set_state_cancel()

    def action_demand_approve_application(self):
        self.with_context(force_sent_mail=False)._set_state_open()
    
    @api.model_create_multi
    def create(self, vals_list):
        demands = super().create(vals_list)
        for i, demand in enumerate(demands):
            Application = self.env['request.application'].sudo()
            action =  self.env.ref('dobtor_demand_application.action_demand_reject')
            if action.active:
                application = Application.create({
                    'res_id': demand.id,
                    'action_id':action.id,
                    'note': action.apply_text_template,
                    'send_mail_partner_id': demand.organizer_id.id,
                    'partner_id': demand.event_creator_partner.id,
                })
        return demands
    # endregion

    def set_state_closed(self, post={}):
        Application = self.env['request.application'].sudo()
        action =  self.env.ref('dobtor_demand_application.action_demand_creator_closed')
        if action.active:
            application = Application.create({
                'res_id': self.id,
                'action_id':action.id,
                'note':post.get('note',False),
                'send_mail_partner_id': self.organizer_id.leader_id.id,
                'partner_id': self.event_creator_partner.id,
                'auditor': self.env.user.id,
                'state': 'cancel',
            })
            if action.auto_confirm:
                application.action_do('reject')
                application.application_cancel_notify()
        else:
            self._set_state_closed()

    def action_demand_creator_closed_application(self):
        self.with_context(force_sent_mail=False)._set_state_closed()

    # region : 待刪除
    # TODO : 帶刪除將由 closed 事件取代
    def set_state_give_up(self, post={}):
        Application = self.env['request.application'].sudo()
        action =  self.env.ref('dobtor_demand_application.action_demand_give_up')
        if action.active:
            application = Application.create({
                'res_id': self.id,
                'action_id':action.id,
                'note':post.get('note',False),
                'send_mail_partner_id': self.organizer_id.leader_id.id,
                'partner_id': self.event_creator_partner.id,
                'related_partner_ids': self.organizer_id.id,
                'auditor': self.env.user.id,
                'state': 'cancel',
            })
            if action.auto_confirm:
                application.action_do()
                application.application_cancel_notify()
        else:
            self._set_state_give_up()

    def action_demand_give_up_application(self):
        self.with_context(force_sent_mail=False)._set_state_give_up()
    # endregion