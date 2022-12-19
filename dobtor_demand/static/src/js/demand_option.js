odoo.define('dobtor_demand.demand_option', function (require) {
    'use strict';
    
    var publicWidget = require('web.public.widget');
    var core = require('web.core');
    var _t = core._t;


    publicWidget.registry.DemandOptions = publicWidget.Widget.extend({
        selector: '.demand_record__header_operate_wrapper',
        events: {
            'click .closed': '_onClosedClick',
            'click .give_up': '_onGiveUpClick',
        },

        start: function () {
            return this._super.apply(this, arguments);
        },

        _onClosedClick: function (ev) {
            var $target = $(ev.currentTarget);
            var demand_id = $target.closest('.demand_record__header_operate_wrapper').data('demand_id');
            $('a.closed, a.give_up').css('pointer-events', 'none');
            $('a.closed, a.give_up').css('opacity', 0.65);

            return this._rpc({
                route: '/demand/option',
                params: {'closed': true, 'demand_id': demand_id,},
            }).then(function (result) {
                if (result)
                    window.location.reload();
            });
        },

        _onGiveUpClick: function (ev) {
            var $target = $(ev.currentTarget);
            var demand_id = $target.closest('.demand_record__header_operate_wrapper').data('demand_id');
            $('a.closed, a.give_up').css('pointer-events', 'none');
            $('a.closed, a.give_up').css('opacity', 0.65);

            return this._rpc({
                route: '/demand/option',
                params: {'give_up': true, 'demand_id': demand_id,},
            }).then(function (result) {
                if (result)
                    window.location.reload();
            });
        },
    });

    return  {
        DemandOptions: publicWidget.registry.DemandOptions,
    };
});