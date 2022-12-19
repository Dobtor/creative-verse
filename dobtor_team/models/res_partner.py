# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from werkzeug import urls
import werkzeug.urls
from odoo.addons.http_routing.models.ir_http import slug
from odoo.osv.expression import AND, OR

class ResPartner(models.Model):
    _inherit = "res.partner"

    is_team = fields.Boolean(
        string='is team',
        default=False
    )
    team_title = fields.Many2one('team.title')
    team_member_ids = fields.Many2many(
        string='Team member',
        comodel_name='res.partner',
        relation='team_meber_rel',
        column1='res_partner_id',
        column2='team_id',
        domain=[('is_team', '=', False)]
    )
    team_join_ids = fields.Many2many(
        string='Team',
        comodel_name='res.partner',
        relation='team_meber_rel',
        column1='team_id',
        column2='res_partner_id',
        domain=[('is_team', '=', True)]
    )
    member_count = fields.Integer(string='Member Count',compute="_compute_member_count")
    @api.depends('team_member_ids')
    def _compute_member_count(self):
        for team in self.filtered('is_team'):
            team.member_count = len(team.team_member_ids)

    apply_ids = fields.One2many(
        string='Apply List',
        comodel_name='member.apply.list',
        inverse_name='partner_id',
    )
    apply_count = fields.Integer(string='Apply Count',compute="_compute_apply_count")
    @api.depends('apply_ids')
    def _compute_apply_count(self):
        for team in self.filtered('is_team'):
            team.apply_count = len(team.apply_ids)
    
    leader_id = fields.Many2one(
        string='Leader',
        comodel_name='res.partner',
        domain=[('is_team', '=', False)]
    )
    leader_title_display = fields.Char('Leader Title', related='leader_id.title.name')
    parents_id = fields.Many2one(
        string='parents team',
        comodel_name='res.partner',
        domain=[('is_team', '=', True)]
    )
    # team_title_display > 沒有人用到的欄位 但不知道是否有機器還存著
    team_title_display = fields.Char('Team Title Display', related='parents_id.team_title.name')
    parents_domain_ids = fields.Many2many('res.partner', compute="_compute_parents_domain_ids")
    assistant_ids = fields.Many2many(
        string='Assistants',
        comodel_name='res.partner',
        relation='leader_assistant_rel',
        column1='leader_id',
        column2='assistant_id',
        domain=[('is_team', '=', False)]
    )

    team_names = fields.Char('Teams', compute="compute_team_display", store=True)

    @api.depends('team_join_ids')
    def compute_team_display(self):
        for record in self:
            if record.team_join_ids:
                team_names = ','.join([team.name for team in record.team_join_ids])
            else:
                team_names = ""
            record.team_names = team_names

    def _compute_parents_domain_ids(self):
        for record in self:
            if record.is_team and record._origin:
                parents_id_domain = record
                parents = record.env['res.partner'].search([('parents_id', '=', record._origin.id)])

                for parent in parents:
                    parent_child = record.env['res.partner'].search([('parents_id', 'child_of', parent.id)])
                    parents_id_domain += parent_child

                record.parents_domain_ids = parents_id_domain
            else:
                record.parents_domain_ids = False

    @api.onchange('is_team')
    def _onchange_is_team(self):
        self._compute_parents_domain_ids()

    @api.model
    def _get_with_user_partner(self, fields):
        user = self.env['res.users'].sudo()
        partner_ids = user.search([]).read(['partner_id'])
        return [(fields ,'=', [partner['partner_id'][0] for partner in partner_ids])]

    @api.model_create_multi
    def create(self, vals_list):
        # TODO : child team mebmer
        partners = super().create(vals_list)
        website = self.env['website'].get_current_website()
        for partner in partners:
            if partner.is_team:
                if not partner.image_1920 and website.customize_default_avatar:
                    partner.image_1920 = website.signup_default_avatar
                if website.customize_default_section:
                    partner.profile_section = website.signup_default_section
            # region : Hande Member
            member_ids = partner.team_member_ids
            if len(member_ids) > 0:
                partner.message_subscribe(member_ids.ids)
            # endregion
            # region : Handle Leader
            leader_id = self.leader_id.id
            if leader_id:
                self.message_subscribe([leader_id])
            # endregion
        return partners

    def write(self, vals):
        # TODO : child team mebmer
        # region : Hande Member
        member_ids = vals.get('team_member_ids', [])
        if len(member_ids) > 0:
            self.message_unsubscribe(self.message_partner_ids.ids)
            self.message_subscribe(member_ids[0][2])  
        # endregion
        # region : Hande Leader
        leader_id = vals.get('leader_id', False)
        if leader_id:
            self.message_subscribe([leader_id])
        if leader_id == False:
            self.message_unsubscribe([self.leader_id.id])
        # endregion
        return super().write(vals)

    def action_member_kick(self, member, post={}):
        new_assistants = self.assistant_ids - member
        new_members = self.team_member_ids - member
        return new_assistants, new_members

    def action_member_to_assistant(self, member, post={}):
        new_assistants = self.assistant_ids + member
        new_members = self.team_member_ids - member
        return new_assistants, new_members

    def action_member_to_member(self, member, post={}):
        new_assistants = self.assistant_ids - member
        new_members = self.team_member_ids + member
        return new_assistants, new_members
    
    @api.depends('referral_key')
    def _compute_referral_url(self):
        super()._compute_referral_url()
        for team in self.filtered('is_team'):
            base_url = self.env['ir.config_parameter'].get_param('web.base.url')
            profile_url =  "/user/profile/%s" % slug(team)
            url = urls.url_join(base_url, profile_url)
            team.referral_url = url
            team.referral_qrcode = '/report/barcode/?type=%s&value=%s&width=%s&height=%s&humanreadable=1' % ('QR', werkzeug.urls.url_quote_plus(url), 128, 128)

    def notify_receiver(self, subject, body, sender, receiver):
        email_from = sender
        email_to = receiver
        if email_from and email_to:
            self._sent_state_mail(subject, body, email_to, email_from)

    def notify_apply_to_join(self, team):
        if not team:
            return
        for rec in self:
            subject = f"User {rec.name} apply to join team {team.name}."
            body = f"User {rec.name} apply to join team {team.name}, please waiting for approval"
            rec.notify_receiver(subject, body, rec.company_id.email, team.leader_id.email)
            body = f"User {rec.name} apply to join team {team.name}."
            rec.notify_receiver(subject, body, team.company_id.email, rec.email)

    def action_member_approve(self, partner, post={}):
        member_apply = self.env['member.apply.list'].sudo().search([('partner_id', '=', post.get('organizer_id')), ('member_id', '=', post.get('member_id'))])
        member_apply.action_apply()
        self.__notify_approve_application(partner)

    def __notify_approve_application(self, partner):
        if not partner:
            return
        for rec in self:
            subject = f"Team {rec.name} approve your application."
            body = f"Team {rec.name} approve your application."
            rec.notify_receiver(subject, body, rec.company_id.email, partner.email)

    def action_member_reject(self, partner, post={}):
        member_apply = self.env['member.apply.list'].sudo().search([('partner_id', '=', post.get('organizer_id')), ('member_id', '=', post.get('member_id'))])
        member_apply.unlink()
        self.__notify_reject_application(partner)

    def __notify_reject_application(self, partner):
        if not partner:
            return
        for rec in self:
            subject = f"Team {rec.name} reject your application."
            body = f"Team {rec.name} reject your application."
            rec.notify_receiver(subject, body, rec.company_id.email, partner.email)

    def notify_leave_team(self, partner):
        if not partner: 
            return
        for rec in self:
            subject = f"User {partner.name} has leave team {rec.name}."
            body = f"User {partner.name} has leave team {rec.name}."
            rec.notify_receiver(subject, body, rec.company_id.email, partner.email)

    def _sent_state_mail(self, subject, body, email_to, email_from):
        if isinstance(self.id, models.NewId) and self._origin.id:
            self = self._origin
        for record in self:
            template = self.env.ref('dobtor_team.team_member_notify_mail', raise_if_not_found=False)
            if template:
                email_values = {
                    'email_to': email_to, 
                    'email_from': email_from,
                    'subject': subject
                }
                template.with_context(body=body).send_mail(record.id, email_values=email_values, force_send=True, raise_exception=False)

    # region : check_access_rights_via_team
    def operation_1_domain(self):
        return [('leader_id','=', self.id)]

    def operation_2_domain(self):
        return [('assistant_ids','in', [self.id])]

    def operation_3_domain(self):
        return OR([self.operation_1_domain(), self.operation_2_domain()])

    def operation_4_domain(self):
        return [('team_member_ids', 'in', [self.id])]
    
    def operation_5_domain(self):
        return OR([self.operation_1_domain(), self.operation_4_domain()])
    
    def operation_6_domain(self):
        return OR([self.operation_2_domain(), self.operation_4_domain()])

    def operation_7_domain(self):
        return OR([self.operation_1_domain() ,OR([self.operation_2_domain(), self.operation_4_domain()])])

    def check_access_rights_common_domain(self):
        return [('is_team', '=', True)]
   
    def check_access_rights_via_team(self, operation, force_domain_fcn=''):
        """ 
            針對當前角色做{顯示}權限的檢查, 類似官方的 check_access_rights 只是針對顯示做處理
            其中 operation 輸入為整數
                team leader = 1,
                team assistant = 2,
                team member = 4,
        """
        self.ensure_one()
        operation_list = {
            '1' : 'operation_1_domain',
            '2' : 'operation_2_domain',
            '3' : 'operation_3_domain', # 1+2
            '4': 'operation_4_domain', 
            '5': 'operation_5_domain', # 1+4
            '6': 'operation_6_domain', # 2+4
            '7': 'operation_7_domain', # 1+2+4
        }
        fcn_name = operation_list.get(str(operation) ,force_domain_fcn)
        if hasattr(self, fcn_name):
            domain = getattr(self, fcn_name)()
        if len(self.search(self.check_access_rights_common_domain() + domain)):
            return True
        return False
    # endregion

class MemberApplyList(models.Model):
    _name = 'member.apply.list'
    _description = "Member Apply List"

    partner_id= fields.Many2one(
        string='team',
        comodel_name='res.partner',
    )
    member_id= fields.Many2one(
        string='applicant',
        comodel_name='res.partner',
        domain=lambda self: self.except_this_team_member(),
        ondelete='set null',
    )

    def except_this_team_member(self):
        partner_id = self.env['res.partner'].browse(self._context.get('default_partner_id'))
        return [('is_team','=',False), ('id', 'not in', partner_id.team_member_ids.ids)]

    def action_apply(self):
        for member in self:
            new_member = member.partner_id.team_member_ids.ids + [member.member_id.id]
            member.partner_id.write({
                'team_member_ids' : [(6, 0 , new_member)]
            })
            member.unlink()

class PartnerTitle(models.Model):
    _inherit = 'res.partner.title'

    partner_ids = fields.One2many(
        string='Partner',
        comodel_name='res.partner',
        inverse_name='title',
    )

class TeamTitle(models.Model):
    _name = "team.title"
    _description = "Team Title"
    _order = "sequence"

    sequence = fields.Integer(string='Sequence', help="Gives the sequence order when displaying a list of analytic distribution")
    name = fields.Char(string='Name', required=True, translate=True)
    partner_ids = fields.One2many(
        string='Team',
        comodel_name='res.partner',
        inverse_name='team_title',
        domain=[('is_team', '=', True)],
    )
    
class ResUsers(models.Model):
    _inherit = 'res.users'

    def get_partner_management_domain(self):
        domain = super().get_partner_management_domain()
        return domain + [('is_team','=',False)]