odoo.define('dobtor_team.team_member_option', function (require) {
    'use strict';
    
    var publicWidget = require('web.public.widget');
    var core = require('web.core');
    var _t = core._t;


    publicWidget.registry.TeamMemberOptions = publicWidget.Widget.extend({
        selector: '.team_profile__members_wrapper',
        events: {
            'click .apply_approve, .audit_approve': '_onApproveClick',
            'click .apply_reject, .audit_reject': '_onRejectClick',
            'click .member_to_assistant': '_onToAssistantClick',
            'click .assistant_to_member': '_onToMemberClick',
            'click .member_kick': '_onKickClick',
        },

        start: function () {
            this.organizer_id = this.$el.data('organizer_id');
            return this._super.apply(this, arguments);
        },

        _onApproveClick: function (ev) {
            var $target = $(ev.currentTarget);
            if ($target.hasClass('audit_approve')) {
                $('.audit_approve, .audit_reject').css('pointer-events', 'none');
                $('.audit_approve, .audit_reject').css('opacity', 0.65);
            }

            return this._rpc({
                route: '/member/option',
                params: {'approve': true, 'member_id': $target.data('member_id'), 'organizer_id': this.organizer_id,},
            }).then(function (result) {
                if (result)
                    window.location.reload();
            });
        },

        _onRejectClick: function (ev) {
            var $target = $(ev.currentTarget);
            if ($target.hasClass('audit_reject')) {
                $('.audit_approve, .audit_reject').css('pointer-events', 'none');
                $('.audit_approve, .audit_reject').css('opacity', 0.65);
            }

            return this._rpc({
                route: '/member/option',
                params: {'reject': true, 'member_id': $target.data('member_id'), 'organizer_id': this.organizer_id,},
            }).then(function (result) {
                if (result)
                    window.location.reload();
            });
        },

        _onToAssistantClick: function (ev) {
            var $target = $(ev.currentTarget);

            return this._rpc({
                route: '/member/option',
                params: {'to_assistant': true, 'member_id': $target.data('member_id'), 'organizer_id': this.organizer_id,},
            }).then(function (result) {
                if (result)
                    window.location.reload();
            });
        },

        _onToMemberClick: function (ev) {
            var $target = $(ev.currentTarget);

            return this._rpc({
                route: '/member/option',
                params: {'to_member': true, 'member_id': $target.data('member_id'), 'organizer_id': this.organizer_id,},
            }).then(function (result) {
                if (result)
                    window.location.reload();
            });
        },

        _onKickClick: function (ev) {
            var $target = $(ev.currentTarget);

            return this._rpc({
                route: '/member/option',
                params: {'kick': true, 'member_id': $target.data('member_id'), 'organizer_id': this.organizer_id,},
            }).then(function (result) {
                if (result)
                    window.location.reload();
            });
        },
    });

    return  {
        TeamMemberOptions: publicWidget.registry.TeamMemberOptions,
    };
});