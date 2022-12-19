from ast import Store
from email.policy import default
from urllib import request
import odoo
from odoo import api, fields, models, tools, SUPERUSER_ID, _
import logging
_logger = logging.getLogger(__name__)

class RequestApplication(models.Model):
    _name = 'request.application'
    _description = 'Request Application'
    _order = "create_date desc"

    action_id = fields.Many2one('request.action', string="Action", required=True)
    partner_id = fields.Many2one(
        'res.partner', 
        string="Record", 
    )
    # region : 收件者
    # TODO : 若日後需要更多的人接收到通知, 有幾個辦法
    # 1. 關聯 Channel, 由 channel 管理通知群 (可以設計 M2M, ex. 一次通知多的channel)
    # 2. 關聯 groups,  由 groups  管理通知群 (可以設計 M2M, ex. 一次通知多的groups)
    # 3. 將欄位修改成 M2M (一次通知該動作要通知的人)
    related_partner_ids = fields.Many2one(
        'res.partner', 
        string="Record (C.C)", 
    )
    send_mail_partner_id = fields.Many2one(
        'res.partner', 
        string="Sent Mail Partner", 
    )
    # endregion
    res_model = fields.Char(
        'Related Model',
        index=True, 
        related='action_id.model_id.model', 
        compute_sudo=True, 
        store=True, 
        readonly=True
    )
    res_id = fields.Many2oneReference(
        string='Related Record', 
        index=True, 
        required=True, 
        model_field='res_model'
    )
    name = fields.Char(
        string='Object',
        compute='_compute_res_name',
        compute_sudo=True,
        store=True,
        readonly=True
    )
    # region : 依賴關聯
    # 除了該模組的審核運作, 我們在這邊設計可以允許一個關聯的依賴關聯
    rel_model_id = fields.Many2one('ir.model', 
        string='Depends Model', 
        help="depends model")
    rel_model = fields.Char( 
        string='Depends Model', 
        related='rel_model_id.model', 
        help="depends model")
    rel_id = fields.Many2oneReference(
        string='Depends Record',
        model_field='rel_model'
    )
    rel_name = fields.Char(
        string='Depends Record',
        compute='_compute_rel_name',
        compute_sudo=True,
        store=True,
        readonly=True
    )
    # endregion
    mode = fields.Selection(
        string='mode',
        selection=[('action', 'Application'), ('record', 'Only record')],
        default='record'
    )
    note = fields.Text(string='Note')
    auditor = fields.Many2one('res.users',string="Operator")
    auditor_id = fields.Many2one(
        'res.partner',
        string="Operator",
        related='auditor.partner_id', 
        store=True
    )
    state = fields.Selection(
        string='Status',
        selection=[('draft', 'Apply'), ('confirm', 'Confirm'), ('cancel','Cancel')],
        default="draft",
        required=True,
    )
    # 因為每筆資料都會有歷程不在需要兩個欄位來紀錄, 原因和拒絕原因
    reject_reason = fields.Text(string='Origin Note')
    
    @api.depends('res_model', 'res_id')
    def _compute_res_name(self):
        for activity in self:
            activity.name = activity.res_model and \
                self.env[activity.res_model].browse(activity.res_id).display_name

    @api.depends('rel_model', 'rel_id')
    def _compute_rel_name(self):
        for activity in self:
            activity.rel_name = activity.rel_model and \
                self.env[activity.rel_model].browse(activity.rel_id).display_name

    def action_do(self, state=''):
        self.ensure_one()
        model = self.env[self.res_model].sudo()
        if state in {'', 'confirm'}:
            code = self.action_id.code
        elif state == 'draft':
            code = self.action_id.apply_code
        elif state == 'reject':
            code = self.action_id.reject_code
        else:
            code = False
        if code:
            if hasattr(model, code):
                if self.rel_model:
                    rel_model = self.env[self.rel_model].sudo()
                    rel_record = rel_model.browse(self.rel_id)
                    res_model = model.browse(self.res_id)
                    getattr(res_model, code)(rel_record)
                else:
                    res_model = model.browse(self.res_id)
                    getattr(res_model, code)()

    def action_confirm(self):
        for record in self:
            record.action_do()
            # 動作變成新的紀錄，需要修改狀態和時間
            new_record = record.copy({
                'auditor': self.env.user.id,
                'state': 'confirm'
            })
            # 將就的紀錄保留下來
            record.write({
                'mode': 'record'
            })
            new_record.application_confirm_notify()
        return     
    
    def application_confirm_notify(self):
        for record in self:
            template = self.env.ref('dobtor_request_application.application_notify_mail', raise_if_not_found=False)
            notic_type = record.action_id.notic_type
            if not notic_type : notic_type = 'text'

            if template and notic_type == 'text':
                subject = record.action_id.name
                body = _("Note：") + record.note
                email_values = {
                    'email_to': record.send_mail_partner_id.email, 
                    'email_from': record.auditor.partner_id.email,
                    'subject': subject,
                }
                template.with_context(body=body).send_mail(record.id, email_values=email_values, force_send=True, raise_exception=False)
            elif notic_type == 'email':
                template = record.confirmation_template_id
                if template:
                    email_values = {
                        'email_to': record.send_mail_partner_id.email, 
                        'email_from': record.auditor.partner_id.email,
                    }
                    template.send_mail(record.id, email_values=email_values, force_send=True, raise_exception=False)

    def application_cancel_notify(self):
        for record in self:
            template = self.env.ref('dobtor_request_application.application_notify_mail', raise_if_not_found=False)
            notic_type = record.action_id.apply_notic_type
            if not notic_type : notic_type = 'text'

            if template and notic_type == 'text':
                subject = record.action_id.name + _(" has canceled.")
                body = _("Reject Reason：") + record.note
                email_values = {
                    'email_to': record.send_mail_partner_id.email, 
                    'email_from': record.auditor.partner_id.email,
                    'subject': subject,
                }
                template.with_context(body=body).send_mail(record.id, email_values=email_values, force_send=True, raise_exception=False)
            elif notic_type == 'email':
                template = record.reject_confirmation_template_id
                if template:
                    email_values = {
                        'email_to': record.send_mail_partner_id.email, 
                        'email_from': record.auditor.partner_id.email,
                    }
                    template.send_mail(record.id, email_values=email_values, force_send=True, raise_exception=False)

    def application_apply_notify(self, send_email_to=None):
        for record in self:
            template = self.env.ref('dobtor_request_application.application_notify_mail', raise_if_not_found=False)
            notic_type = record.action_id.apply_notic_type
            if not notic_type : notic_type = 'text'

            if self.env.company.email:
                if template and notic_type == 'text':
                    subject = record.action_id.name + _(" has apply.")
                    body = _("Note：") + record.note
                    email_values = {
                        'email_to': send_email_to or ','.join({record.send_mail_partner_id.email, record.related_partner_ids.email}), 
                        'email_from': self.env.company.email,
                        'subject': subject,
                    }
                    template.with_context(body=body).send_mail(record.id, email_values=email_values, force_send=True, raise_exception=False)
                elif notic_type == 'email':
                    template = record.reject_confirmation_template_id
                    if template:
                        email_values = {
                            'email_to': send_email_to or ','.join({record.send_mail_partner_id.email, record.related_partner_ids.email}), 
                            'email_from': self.env.company.email,
                        }
                        template.send_mail(record.id, email_values=email_values, force_send=True, raise_exception=False)

class RequestAction(models.Model):
    _name = 'request.action'
    _description = 'Request Action'
    # TODO : (想法) 這邊可以做 flow, 當然如果做 flow 相對應的程式碼也要跟著變動
    # 若要做 flow 可以參考倉庫對於產品庫存拉式和推式, 在產品上的流程

    name = fields.Char(string='Action Name', required=True, translate=True)
    model_id = fields.Many2one('ir.model', string='Model', required=True, ondelete='cascade',
                               help="Model on which the server action runs.")
    
    auto_confirm = fields.Boolean(
        string='auto confirm',
        default=False
    ) 
    active = fields.Boolean(
        string='Active',
        default=True
    )
    # region : confirm
    # TODO : 目前會用這樣的設計是因為, 目前只有三個狀態如果有需要異動則需要再改進
    code = fields.Text(string='Python Code', groups='base.group_system',
                       help="Write Python code that the action will execute. Some variables are "
                            "available for use; help about python expression is given in the help tab.")
    notic_type = fields.Selection(
        string='Notice',
        selection=[
            ('no_notic_type', 'No Notice'), 
            ('email', 'Email Template'),
            ('text', 'Text Template')
        ],
        default="text"
    )
    text_template = fields.Text(
        string='Text Template',
        translate=True,
    )
    confirmation_template_id = fields.Many2one(
        'mail.template', 
        string='Confirmation Email',
        domain="[('model', '=', 'request.application')]",
        default=lambda self: self.env.ref('dobtor_request_application.application_notify_mail', raise_if_not_found=False)
    )
    #endregion

    # region : reject
    reject_code = fields.Text(
        string='Python Code', 
        groups='base.group_system'
    )
    reject_notic_type = fields.Selection(
        string='Notic',
        selection=[
            ('no_notic_type', 'No Notice'), 
            ('email', 'Email Template'),
            ('text', 'Text Template')
        ],
        default="text"
    )
    reject_text_template = fields.Text(
        string='Text Template',
        translate=True,
    )
    reject_confirmation_template_id = fields.Many2one(
        'mail.template', 
        string='Confirmation Email',
        domain="[('model', '=', 'request.application')]",
        default=lambda self: self.env.ref('dobtor_request_application.application_notify_mail', raise_if_not_found=False)
    )
    #endregion

    # region : apply
    apply_code = fields.Text(
        string='Python Code', 
        groups='base.group_system'
    )
    apply_notic_type = fields.Selection(
        string='Notic',
        selection=[
            ('no_notic_type', 'No Notice'), 
            ('email', 'Email Template'),
            ('text', 'Text Template')
        ],
        default="text"
    )
    apply_text_template = fields.Text(
        string='Text Template',
        translate=True,
    )
    apply_confirmation_template_id = fields.Many2one(
        'mail.template', 
        string='Confirmation Email',
        domain="[('model', '=', 'request.application')]",
        default=lambda self: self.env.ref('dobtor_request_application.application_notify_mail', raise_if_not_found=False)
    )
    #endregion

    @api.model
    def get_active(self, action_data_id):
        action = self.env.ref(action_data_id)
        return action.active


