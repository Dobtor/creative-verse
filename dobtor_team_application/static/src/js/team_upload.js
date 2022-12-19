odoo.define('dobtor_team_application.team_upload', function (require) {
    "use strict";

    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var team_upload = require('dobtor_team.team_upload');
    var _t = core._t;


    team_upload.TeamUpload.include({
        start: function () {
            var defs = [this._super.apply(this, arguments)];
            this.unpublish_counts = this.$el.data('unpublish_counts') || 0;
            return Promise.all(defs);
        },
        _openDialog: function ($element) {
            if (this.unpublish_counts > 0)
                return this._onConstraintClick($element);
            else 
                return this._super.apply(this, arguments);
        },
        _onConstraintClick: function ($element) {
            const dialog = new Dialog(this, {
                title: _t('Create team constraint'),
                size: 'medium',
                $content: $('<div/>', {text: _t('Unable to create a team, you need to complete team authentication to create a new team')}),
                buttons: [{
                    text: _t("Cancel"),
                    close: true,
                }],
            });
            dialog.on('closed', this, function () {
                $element.css('pointer-events', 'unset');
                $element.css('opacity', 'unset');
            });
            return dialog.open();
        },
    });
});