odoo.define('dobtor_team.team_apply', function (require) {
    'use strict';
    
    var publicWidget = require('web.public.widget');
    var core = require('web.core');
    var _t = core._t;


    publicWidget.registry.TeamApply = publicWidget.Widget.extend({
        selector: '.js_team_apply',
        events: {
            'click': '_onClick',
        },

        start: function () {
            return this._super.apply(this, arguments);
        },

        _onClick: function (ev) {
            var $target = $(ev.currentTarget);
            
            $target.addClass('team_btn--disabled');
            return this._rpc({
                route: '/team/apply_confirm',
                params: {'organizer_id': $target.data('organizer_id')},
            }).then(function (modal) {
                var $modal = $(modal);
                $modal.modal({backdrop: 'static', keyboard: false});
                $modal.on('click', '.reload', function () {
                    window.location.reload();
                });
            });
        },
    });

    publicWidget.registry.TeamCancelApply = publicWidget.Widget.extend({
        selector: '.js_team_cancel_apply',
        events: {
            'click': '_onClick',
        },

        start: function () {
            return this._super.apply(this, arguments);
        },

        _onClick: function (ev) {
            var self = this;
            var $target = $(ev.currentTarget);
            
            $target.addClass('team_btn--disabled');
            return this._rpc({
                route: '/team/cancel_apply_modal',
                params: {},
            }).then(function (modal) {
                var $modal = $(modal);
                $modal.modal();
                $modal.on('click', '.confirm', function () {
                    return self._rpc({
                        route: '/team/cancel_apply_confirm',
                        params: {'organizer_id': $target.data('organizer_id')},
                    }).then(function (result) {
                        $modal.find('.double_check').toggleClass('d-none', true);
                        $modal.find('.success_display').toggleClass('d-none', false);

                        $modal.data('bs.modal')._config.backdrop = 'static';
                        $modal.off('keydown.dismiss.bs.modal');
                    });
                });

                $modal.on('click', '.reload', function () {
                    window.location.reload();
                });

                $modal.on('hidden.bs.modal', function (e) {
                    $modal.remove();
                    $target.removeClass('team_btn--disabled');
                });
            });
        },
    });

    publicWidget.registry.TeamLeave = publicWidget.Widget.extend({
        selector: '.js_team_leave',
        events: {
            'click': '_onClick',
        },

        start: function () {
            return this._super.apply(this, arguments);
        },

        _onClick: function (ev) {
            var self = this;
            var $target = $(ev.currentTarget);
            
            $target.addClass('team_btn--disabled');
            return this._rpc({
                route: '/team/leave_modal',
                params: {},
            }).then(function (modal) {
                var $modal = $(modal);
                $modal.modal();
                $modal.on('click', '.confirm', function () {
                    return self._rpc({
                        route: '/team/leave_confirm',
                        params: {'organizer_id': $target.data('organizer_id')},
                    }).then(function (result) {
                        $modal.find('.double_check').toggleClass('d-none', true);
                        $modal.find('.success_display').toggleClass('d-none', false);

                        $modal.data('bs.modal')._config.backdrop = 'static';
                        $modal.off('keydown.dismiss.bs.modal');
                    });
                });

                $modal.on('click', '.reload', function () {
                    window.location.reload();
                });

                $modal.on('hidden.bs.modal', function (e) {
                    $modal.remove();
                    $target.removeClass('team_btn--disabled');
                });
            });
        },
    });

    return  {
        TeamApply: publicWidget.registry.TeamApply,
        TeamCancelApply: publicWidget.registry.TeamCancelApply,
        TeamLeave: publicWidget.registry.TeamLeave,
    };
});