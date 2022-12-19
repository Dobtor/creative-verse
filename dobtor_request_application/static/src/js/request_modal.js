odoo.define('dobtor_request_application.request_common', function (require) {
    'use strict';

    const core = require('web.core');
    const Dialog = require('web.Dialog');
    const serializeformMixin = require('dobtor_website_tool.serializeform');
    const _t = core._t;
    const qweb = core.qweb;

    let requestDialog = Dialog.extend(serializeformMixin, {
        xmlDependencies: (Dialog.prototype.xmlDependencies || []).concat(
            ['/dobtor_request_application/static/src/xml/request_modal.xml']
        ),
        template: 'dobtor.request.description.modal',
        events: _.extend({}, Dialog.prototype.events, {
        }),
        init: function (parent, options) {
            let buttons = [{
                text: _t("Save"),
                classes: 'ml-auto bg-o-color-1 save_disable',
                click: this._onClick.bind(this)
            },
            {
                text: _t("Discard"),
                classes: 'save_disable',
                close: true
            },
            ];
            this._super(parent, _.extend({}, {
                title: options.title,
                size: 'medium',
                buttons: buttons,
            }, options || {}));
            this.options = options;
        },
        start: function () {
            this.$modal.find(".modal-header")
            this.$footer.prepend('<div class="d-flex flex-column footer_error_msg w-100 mb-3"/>');
            var $component = $(qweb.render(
                this.options.template,
                { options: this.options }
            ));
            this.$el.find('form').append($component);
            let defs = [];
            defs.push(this._super.apply(this, arguments));
            return Promise.all(defs);
        },
        get_value: function () {
            const formArray = this.$el.find('form').serializeArray();
            return this.objectifyForm(formArray);
        },
        _alertDisplay: function (message) {
            this.$footer.find('.footer_error_msg').append(
                $('<div/>', {
                    "class": 'alert alert-warning',
                    id: 'upload-alert',
                    role: 'alert'
                }).text(message)
            );
        },
        disableButton: function (button) {
            $("body").block({ overlayCSS: { backgroundColor: "#000", opacity: 0, zIndex: 1050 }, message: false });
            $(button).attr('disabled', true);
            $(button).prepend('<span class="o_loader"><i class="fa fa-refresh fa-spin"></i>&nbsp;</span>');
        },
        _onClick: function (ev) {
            let self = this;
            let $target = $(ev.currentTarget);
            this.$footer.find('.footer_error_msg').empty();
            if (this.$el.find('form')[0].checkValidity()) {
                let value = this.get_value();
                this.disableButton($target);
                return this._rpc({
                    route: self.options.route,
                    params: value,
                }).then(function (result) {
                    if (result)
                        window.location.reload();
                });
            } else {
                this._alertDisplay(_t('Please fill out Description.'));
            }
        },
    })
    return {
        requestDialog: requestDialog,
    };
});