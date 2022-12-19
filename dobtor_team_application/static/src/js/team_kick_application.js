odoo.define('dobtor_team_application.team_kick_application', function (require) {
    'use strict';

    const core = require('web.core');
    const request_common = require('dobtor_request_application.request_common');
    const team_member = require('dobtor_team.team_member_option');
    const _t = core._t;

    team_member.TeamMemberOptions.include({
        xmlDependencies: (team_member.TeamMemberOptions.prototype.xmlDependencies || []).concat(
            [
                '/dobtor_team_application/static/src/xml/kick_modal.xml',
            ]
        ),
        _openkickDialog: function ($element) {
            let data = $element.data();
            data = _.extend({}, data, {
                'kick': true,
                'organizer_id': $element.closest('.team_profile__members_wrapper').data('organizer_id'),
                'template': 'dobtor.team.member.kick.modal',
                'route': '/member/option',
                'title': _t("Member Kick"),
            });
            return new request_common.requestDialog(this, data).open();
        },
        _onKickClick: function (ev) {
            ev.stopPropagation();
            ev.preventDefault();
            let $target = $(ev.currentTarget);
            let self = this;
            this._rpc({
                model: 'request.action',
                method: 'get_active',
                args: ['dobtor_team_application.action_remove_from_a_team'],
            }).then(function (result) {
                if (result)
                    self._openkickDialog($target);
                else {
                    self._rpc({
                        route: '/member/option',
                        params: {
                            'kick': true,
                            'organizer_id': $target.closest('.team_profile__members_wrapper').data('organizer_id'),
                            'member_id': $target.data('member_id'),
                        },
                    }).then(function (result) {
                        if (result)
                            window.location.reload();
                    });
                }   
            });

            
        },
    });

});