odoo.define('dobtor_user_profile.profile_user_info_edit', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var core = require('web.core');
    var _t = core._t;
    var qweb = core.qweb;


    publicWidget.registry.profileUserInfoEdit = publicWidget.Widget.extend({
        selector: '#user_info_block',
        events: {
            'click .o_wprofile_info_js_edit': '_onEditClick',
            'click .o_wprofile_edit_submit_btn': '_SaveClick', 
            'click .o_wprofile_edit_js_cancel': '_CancelClick',
            'click button#email_send': 'send_mail',
            'change input[name="country_option"]': '_onCountryOptionChanged',
            'change select[name="country_id"]': '_changeCountry',
        },

        start: function () {
            var self = this;
            this.$container = self.$target;

            return this._super.apply(this, arguments);
        },
    
        _onEditClick: function (ev) {
            var self = this;
            ev.preventDefault();
            return this._rpc({
                route: '/partner/template/display',
                params: { info_edit: true },
            }).then(function (result) {
                self.$container.html("<form id='user_information_edit_form'><input type='hidden' name='csrf_token' value='" + odoo.csrf_token + "'/>" + result + "</form>");
            });
        },

        _formValidateGetValues: function () {
            var post = {}
            this.$container.find('input').each(function () {
                post[$(this).attr('name')] = $(this).val() || false;
            });
            this.$container.find('select').each(function () {
                post[$(this).attr('name')] = $(this).val();
            });

            if ($('input[name="country_option"]:checked').attr('id') == 'country_taiwan')
                post['country_id'] = $('input[name="country_option"]:checked').data('taiwan_id')
                

            return post;
        },

        _SaveClick: function (ev) {
            var self = this;
            ev.preventDefault();
    
            if (this._formValidate(this.$container.find('form'))) {
                var post = this._formValidateGetValues();
                return this._rpc({
                        route: '/partner/edit/save',
                        params: post,
                    }).then(function (result) {
                        if (result.error_message) {
                            self._alertDisplay(result.error_message);
                            // self.$container.find('input').each(function () {
                            //     if (result.error_field.includes($(this).attr('name'))) {
                            //         $(this).addClass("is-invalid");
                            //     } 
                            // });
                        } else {
                            window.location.reload();
                            // self.$container.html(result);
                        }
                    });
            }
        },

        _CancelClick: function (ev) {
            var self = this;
            ev.preventDefault();
            return this._rpc({
                route: '/partner/template/display',
                params: {},
            }).then(function (result) {
                self.$container.html(result);
            });
        },

        _alertDisplay: function (message) {
            this._alertRemove();
            $('<div/>', {
                "class": 'alert alert-warning',
                id: 'profile-error-alert',
                role: 'alert'
            }).text(message).insertBefore(this.$('form'));
        },

        _alertRemove: function () {
            this.$('#profile-error-alert').remove();
        },

        _formValidate: function ($form) {
            $form.addClass('was-validated');
            return $form[0].checkValidity();
        },

        resend_time: function (target, wait) {
            const self = this
            if (wait == 0) {
                target.removeAttr("disabled");
                target.text("Resend");
            } else {
                target.attr("disabled", true);
                target.text(wait + "s resend");
                wait--;
                setTimeout(function () {
                    self.resend_time(target, wait)
                }, 1000)
            }
        },

        send_mail: function (ev) {
            const self = this;
            let $target = $(ev.currentTarget);
            let mail = this.$container.find("input[name='email']").val().trim();
            if (mail) {
                this.resend_time($target, 30);
                var values = {
                    'email': mail
                };
                this._rpc({
                    route: '/profile/send_email',
                    params: values,
                }).then(function (data) {
                    if (data == '1') {
                        return self.$container.find("input[name='email_verify_code']").removeAttr("disabled");
                    }
                });
            }
        },

        _onCountryOptionChanged: function (ev) {
            let $target = this.$(ev.currentTarget);
            
            $target.attr('id') == 'country_taiwan' ? this._changeState($target.data('taiwan_id')) : this._changeState(this.$("#country_id").val())
            this.$("select[name='country_id']").toggleClass('d-none', $target.attr('id') != 'country_other');
            this.$('.other_country_info_add').toggleClass('d-none', $target.attr('id') != 'country_other');
            this.$(".other_country_info_add input").attr('required', $target.attr('id') == 'country_other');
        },

        _changeCountry: function () {
            if (!this.$("#country_id").val()) {
                return;
            }
            this._changeState(this.$("#country_id").val());
        },

        _changeState: function(country_id) {
            this._rpc({
                route: "/profile/country_infos/" + country_id,
                params: {},
            }).then(function (data) {
                var selectStates = $("select[name='state_id']");
                selectStates.html("<option value=''>" + _t('Counties...') + "</option>");
                if (data.states.length) {
                    _.each(data.states, function (x) {
                        var opt = $('<option>').text(x[1])
                            .attr('value', x[0])
                            .attr('data-code', x[2]);
                        selectStates.append(opt);
                    });
                    selectStates.toggleClass('d-none', false);
                } else {
                    selectStates.toggleClass('d-none', true);
                }
            });
        },
    });

    return {
        profileUserInfoEdit: publicWidget.registry.profileUserInfoEdit,
    };

});