odoo.define('dobtor_demand.demand_registration', function (require) {
    'use strict';

    var WebsiteEvent = require('website_event.website_event');
    var core = require('web.core');
    var QWeb = core.qweb;
    var ajax = require("web.ajax");


    WebsiteEvent.include({

        on_click: function (ev) {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                $(".js_demand_quantity_json").on('click', self._onClickDemandJSON.bind(self));
                $("#modal_demand_attendees_registration").on('hidden.bs.modal', function (e) {
                    $("#modal_demand_attendees_registration").remove();
                });

                $("#confirm_button").on('click', self._submit_form.bind(self));

            });
        },

        _onClickDemandJSON: function (ev) {
            var self = this;
            ev.preventDefault();
            var $link = $(ev.currentTarget);
            var $input = $link.closest('.input-group').find("input");
            var $total_mins = $('.demand_register_total_mins');
            var $total_amount = $('.demand_register_total_amount');
            var min = parseFloat($input.data("min") || 0);
            var max = parseFloat($input.data("max") || Infinity);
            var previousQty = parseFloat($input.val() || 0, 10);
            var quantity = ($link.has(".fa-minus").length ? -1 : 1) + previousQty;
            // self._update_demand_description(price, quantity);
            var newQty = quantity > min ? (quantity < max ? quantity : max) : min;
            if (newQty !== previousQty) {
                $input.val(newQty).trigger('change');
                if ($total_mins.length) {
                    $total_mins.html(newQty * $total_mins.data('mins'));
                }
                if ($total_amount.length) {
                    $total_amount.html(newQty * $total_amount.data('amount'));
                }
            }
            return false;
        },
        _submit_form: function (ev) {
            ev.preventDefault();
            ev.stopPropagation();
            var $form = $(ev.currentTarget).closest('form');
            $form.addClass('was-validated');
            
            if ($form[0].checkValidity()) {
                var post = {
                    'request_qty':$('#request_qty').val(),
                    '1-phone':$('input[name="1-phone"]').val(),
                    '1-event_ticket_id':$('#event_ticket_id').val(),
                };
                $('#confirm_button').attr('disabled',true);
                return ajax.jsonRpc($form.attr('action'), 'call', post).then(function (modal) {
                    $("#modal_demand_attendees_registration").remove();
                    var $modal = $(modal);
                    $modal.modal({backdrop: 'static', keyboard: false});
                    $modal.appendTo('body').modal();
                    $modal.on('click', '.reload', function () {
                        window.location.reload();
                    });
                });
            }
        },

        // _update_demand_description: function (price, quantity) {
        //     $('.compute_price').text(price * quantity);
        //     $('.compute_qty').text(quantity);
        // },
    });

});