# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ResPartner(models.Model):
    _inherit = "res.partner"

    request_application_ids = fields.One2many(
        string='Applications',
        comodel_name='request.application',
        # inverse_name='partner_id',
        compute="_compute_request_application",
        domain="['|',('partner_id', '=', id),('related_partner_ids', '=', id)]",
    )
    application_count = fields.Integer(
        string='Application Count',compute="_compute_application",store=True
    )

    def action_partner_request(self):
        self.ensure_one()
        context = dict(self._context or {})
        return {
            'name': self.name + _(' Record'),
            'domain': [
                "|",
                ('partner_id', '=', self.id),
                ('related_partner_ids', '=', self.id)
            ],
            'context': context,
            'res_model': 'request.application',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'limit': 80,
        }

    def _compute_request_application(self):
        for record in self:
            record.request_application_ids = self.env['request.application'].search(
                [   
                    "|",
                    ('partner_id', '=', record.id),
                    ('related_partner_ids', '=', record.id)
                ])         

    @api.depends('request_application_ids.partner_id')
    def _compute_application(self):
        for record in self:
            record.application_count = len(record.request_application_ids)
