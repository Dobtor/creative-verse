# -*- coding: utf-8 -*-

from odoo import models, fields, api


class RequestReject(models.TransientModel):
    _name = "request.application.reject"
    _description = 'Request Application Reject'

    
    request_id = fields.Many2one(
        comodel_name='request.application',
        string='Request Application'
    )
    action_id = fields.Many2one(
        'request.action', 
        related='request_id.action_id', 
        string="Action", 
    )
    res_model = fields.Char(
        'Related Model',
        related='request_id.res_model', 
    )
    # TODO : 即將被取代的欄位欄位
    partner_id = fields.Many2one(
        'res.partner', 
        related='request_id.partner_id', 
    )
    name = fields.Char(
        string='Record Name',
        related='request_id.name'
    )
    # rel_model_id = fields.Many2one(
    #     'ir.model', 
    #     string='Depends Model', 
    #     related='request_id.rel_model_id',
    #     help="depends model"
    # )
    rel_model = fields.Char( 
        string='Depends Model', 
        related='request_id.rel_model', 
        help="depends model"
    )
    rel_name = fields.Char(
        string='Depends Record',
        related='request_id.rel_name', 
        model_field='rel_model'
    )
    note = fields.Text(
        string='Note',
        related='request_id.note', 
    )
    reject_reason = fields.Text(
        string='Reject Reason'
    )

    def action_cancel(self):
        for record in self:
            # 動作變成新的紀錄
            new_record = record.request_id.copy({
                'auditor':self.env.user.id,
                'state': 'cancel',
                'reject_reason': record.request_id.note,
                'note': record.reject_reason,
            })
            # 將就的紀錄保留下來
            record.request_id.write({
                'mode': 'record'
            })
            new_record.application_cancel_notify()
        return {'type': 'ir.actions.act_window_close'}