odoo.define('dobtor_team_application.team_application', function (require) {
    'use strict';
    
    var publicWidget = require('web.public.widget');
    var core = require('web.core');
    var _t = core._t;
    var ajax = require("web.ajax");

    publicWidget.registry.TeamPublishApplication = publicWidget.Widget.extend({
        selector: "#team_applicaiton",
        events: {
            "click #confirm_button": '_onClick',
        },

        _onClick: function (ev) {
            ev.preventDefault();
            ev.stopPropagation();
            var $form = $(ev.currentTarget).closest('form');
            var post = {
                'partner_id':$("input[name='partner_id']").val(),
                // 'note':$("textarea[name='note']").val(),
            };
            $('#confirm_button').attr('disabled',true);
            return ajax.jsonRpc($form.attr('action'), 'call', post).then(function (modal) {
                $("#team_applicaiton").modal('toggle');
                var $modal = $(modal);
                $modal.modal({backdrop: 'static', keyboard: false});
                $modal.appendTo('body').modal();
            });
        },
    });

    return  {
        TeamPublishApplication: publicWidget.registry.TeamPublishApplication,
    };
});