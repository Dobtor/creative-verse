# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ResPartner(models.Model):
    _inherit = "res.partner"

    # region : check_access_rights_via_team
    def check_access_rights_common_domain(self):
        return [('tag_ids', 'in', [self.env.ref('dobtor_team_application.team_tag_team_publish').id])] + super().check_access_rights_common_domain()
    # endregion

    def action_add_team_access_publish(self):
        tag =  self.env.ref('dobtor_team_application.team_tag_team_publish')
        self.write({
            'tag_ids':[(4,tag.id)]
        })
        # 讓 leader_id 和 assistant_ids 去觸法 write 事件. 
        if self.leader_id:
            self.write({
                'leader_id': self.leader_id.id
            })
        if self.assistant_ids:
            self.write({
                'assistant_ids':[(6, 0, self.assistant_ids.ids)]
            })

    def action_member_kick(self, member, post={}):
        # 不處理 assistant_ids, team_member_ids 由 action_remove_from_a_team 函式處理
        new_assistants = False
        new_members = False

        Appl = self.env['request.application'].sudo()
        action =  self.env.ref('dobtor_team_application.action_remove_from_a_team')
        application = Appl.search([
            ('res_model','=', 'res.partner'),
            ('res_id', '=', self.id),
            ('action_id','=',action.id),
            ('state','=','draft')
        ], limit=1)
        if action.active and not application:
            organizer_id = int(post.get('organizer_id')) if post.get('organizer_id', False) else False
            team = self.env['res.partner'].sudo().browse(organizer_id)
            application = Appl.create({
                'partner_id': team.id,
                'res_id': self.id,
                'action_id':action.id,
                'rel_model_id': self.env.ref('base.model_res_partner').id,
                'rel_id': member.id,
                'note':post.get('note',False),
                'send_mail_partner_id': member.id,
                'auditor': self.env.user.id,
                'state': 'cancel',
                'related_partner_ids': member.id,
            })
            if action.auto_confirm:
                application.action_do('reject')
                application.application_cancel_notify()
        else:
            new_assistants, new_members = super().action_member_kick(member, post)
        return new_assistants, new_members

    def action_remove_from_a_team(self, member):
        new_assistants = self.assistant_ids - member
        new_members = self.team_member_ids - member
        self.write({
            'assistant_ids': [(6, 0, new_assistants.ids)],
            'team_member_ids': [(6, 0, new_members.ids)],
        })


    # region : 管理者操作 (將原本 Dobtor Team 的動作拆解, 並作紀錄)
    def action_member_approve(self, member, post={}):
        Application = self.env['request.application'].sudo()
        action =  self.env.ref('dobtor_team_application.action_member_join_operate_record')
        if action.active:
            organizer_id = int(post.get('organizer_id')) if post.get('organizer_id', False) else False
            team = self.env['res.partner'].sudo().browse(organizer_id)
            application = Application.create({
                'partner_id': team.id,
                'res_id': self.id,
                'action_id':action.id,
                'rel_model_id': self.env.ref('base.model_res_partner').id,
                'rel_id': member.id,
                'note': action.text_template,
                'send_mail_partner_id': member.id,
                'auditor': self.env.user.id,
                'state': 'confirm',
                'related_partner_ids': member.id,
            })
            if action.auto_confirm:
                application.action_do()
                application.application_cancel_notify()
        else:
            super().action_member_approve(member, post)
        

    def action_member_approve_join_team(self, member):
        member_apply = self.env['member.apply.list'].sudo().search([('partner_id', '=', self.id), ('member_id', '=', member.id)])
        member_apply.action_apply()

    def action_member_reject(self, member, post={}):
        Application = self.env['request.application'].sudo()
        action =  self.env.ref('dobtor_team_application.action_member_join_operate_record')
        if action.active:
            organizer_id = int(post.get('organizer_id')) if post.get('organizer_id', False) else False
            team = self.env['res.partner'].sudo().browse(organizer_id)
            application = Application.create({
                'partner_id': team.id,
                'res_id': self.id,
                'action_id':action.id,
                'rel_model_id': self.env.ref('base.model_res_partner').id,
                'rel_id': member.id,
                'note': action.reject_text_template,
                'send_mail_partner_id': member.id,
                'auditor': self.env.user.id,
                'state': 'cancel',
                'related_partner_ids': member.id,
            })
            if action.auto_confirm:
                application.action_do('reject')
                application.application_cancel_notify()
        else:
            super().action_member_reject(member, post)

    def action_member_reject_join_team(self, member):
        member_apply = self.env['member.apply.list'].sudo().search([('partner_id', '=', self.id), ('member_id', '=', member.id)])
        member_apply.unlink()
    # endregin

    # region : 用戶申請目前只有針對, 原本的方法擴充(記下一筆紀錄而已)
    def notify_apply_to_join(self, team):
        Application = self.env['request.application'].sudo()
        action =  self.env.ref('dobtor_team_application.action_member_join_operate_record')
        if action.active:
            application = Application.create({
                'partner_id': self.id,
                'res_id': team.id,
                'action_id':action.id,
                'rel_model_id': self.env.ref('base.model_res_partner').id,
                'rel_id': self.id,
                'note': action.apply_text_template,
                # 'send_mail_partner_id': team.leader_id.id,
                'related_partner_ids': team.id,
            })
            application.application_apply_notify(','.join({team.leader_id.email, self.email}))
        super().notify_apply_to_join(team)
    # endregion