odoo.define('dobtor_user_profile.profile_edit', function (require) {
    'use strict';

    var core = require('web.core');
    var session = require('web.session');
    var Dialog = require('web.Dialog');
    var ajax = require('web.ajax');
    var publicWidget = require('web.public.widget');
    var Widget = require('web.Widget');
    var utils = require('web.utils');

    var QWeb = core.qweb;
    var _t = core._t;

    var ProfileEditDialog = Dialog.extend({
        template: 'website.profile.pop.modal',
        events: _.extend({}, Dialog.prototype.events, {
            'change input#upload': '_onChangeImage',
        }),
        init: function (parent, options) {
            var buttons = [{
                    text: _t("Save"),
                    classes: 'btn-primary save_disable',
                    click: this._onClickFormSubmit.bind(this)
                },
                {
                    text: _t("Discard"),
                    classes: 'mr-auto save_disable',
                    close: true
                },
            ];
            this._super(parent, _.extend({}, {
                title: _t("Profile Edit"),
                size: 'medium',
                buttons: buttons,
            }, options || {}));
            this.partnerId = options.partner_id || false;
            this.editType = options.editType;
            this.file = {};
        },

        willStart: function () {
            var defs = [this._super.apply(this, arguments)];
            var self = this;

            defs.push(this._rpc({
                model: 'res.partner',
                method: 'get_partner_edit_data',
            }).then(function (result) {
                self.old_values = result;
            }));
    
            return Promise.all(defs);
        },
        
        _fileReset: function () {
            var control = this.$('#upload');
            control.replaceWith(control = control.clone(true));
            this.file.name = false;
        },

        _svgToPng: function () {
            var img = this.$el.find('img#profile-image')[0];
            var canvas = document.createElement('canvas');
            canvas.width = img.width;
            canvas.height = img.height;
            canvas.getContext('2d').drawImage(img, 0, 0);
            return canvas.toDataURL('image/png').split(',')[1];
        },

        _onChangeImage: function (ev) {
            var self = this;
            this._alertRemove();
    
            var file = ev.target.files[0];
            if (!file) {
                this.$('#profile-image').attr('src', '#');
                return;
            }
            var isImage = /^image\/.*/.test(file.type);
            this.file.name = file.name;
            this.file.type = file.type;
            if (!isImage) {
                this._alertDisplay(_t("Invalid file type. Please select image file"));
                this._fileReset();
                return;
            }
            if (file.size / 1024 / 1024 > 25) {
                this._alertDisplay(_t("File is too big. File size cannot exceed 25MB"));
                this._fileReset();
                return;
            }

            utils.getDataURLFromFile(file).then(function (buffer) {
                if (isImage) {
                    self.$('#profile-image').attr('src', buffer);
                }
                buffer = buffer.split(',')[1];
                self.file.data = buffer;
            });
        },

        _alertDisplay: function (message) {
            this._alertRemove();
            $('<div/>', {
                "class": 'alert alert-warning',
                id: 'upload-alert',
                role: 'alert'
            }).text(message).insertBefore(this.$('form'));
        },
        _alertRemove: function () {
            this.$('#upload-alert').remove();
        },

        _formGetFieldValue: function (fieldId) {
            return this.$('#' + fieldId).val();
        },
        _formValidate: function () {
            var form = this.$("form");
            form.addClass('was-validated');
            return form[0].checkValidity();
        },

        _formValidateGetValues: function () {
            var values = _.extend({
                'partner_id': this.partnerId,
            });

            if (['section', 'avatar'].includes(this.editType)){
                let field = this.editType === 'section' ? 'profile_section' : 'image_256';
                if (/^image\/.*/.test(this.file.type)) {
                    values[field] = this.file.type === 'image/svg+xml' ? this._svgToPng() : this.file.data;
                }
            }
            else if(this.editType === 'info'){
                _.extend(values, {
                    'name': this._formGetFieldValue('name'),
                    'street': this._formGetFieldValue('street'),
                    'profile_description': this._formGetFieldValue('profile_description'),
                });
            }

            return values;
        },

        _onClickFormSubmit: function (ev) {
            var self = this;

            if (this._formValidate()) {
                var values = this._formValidateGetValues();
                return this._rpc({
                    route: '/profile/edit',
                    params: values,
                }).then(function (data) {
                    self._onFormSubmitDone(data);
                });
            }
        },

        _onFormSubmitDone: function (data) {
            if (data.error) {
                this._alertDisplay(data.error);
            } else {
                window.location = data.url;
            }
        },
    });

    publicWidget.registry.websiteProfileEdit = publicWidget.Widget.extend({
        selector: '.o_wprofile_js_edit',
        xmlDependencies: ['/dobtor_user_profile/static/src/xml/profile_edit.xml'],
        events: {
            'click': '_onEditClick',
        },

        _openDialog: function ($element) {
            var data = $element.data();
            return new ProfileEditDialog(this, data).open();
        },

        _onEditClick: function (ev) {
            ev.preventDefault();
            this._openDialog($(ev.currentTarget));
        },
    });

    // #region: 我的簡介popup編輯
    var ProfileDescForm = Widget.extend({
        start: function () {
            var self = this;
            var res = this._super.apply(this.arguments).then(function () {
                $('#o_wprofile_desc_edit_form .a-submit').click(function (ev) {
                    self.on_click(ev);
                });
            });
            return res;
        },

        on_click: function (ev) {
            ev.preventDefault();
            ev.stopPropagation();
            var self = this;
            var $form = $(ev.currentTarget).closest('form');
            var $button = $(ev.currentTarget);

            $button.css('pointer-events', 'none');
            $button.css('opacity', 0.65);

            return ajax.jsonRpc($form.attr('action'), 'call', {}).then(function (modal) {
                var $modal = $(modal);
                $modal.modal({backdrop: 'static', keyboard: false});
                $modal.appendTo('body').modal();
                $modal.on('hidden.bs.modal', function (e) {
                    $modal.remove();
                    $button.css('pointer-events', 'unset');
                    $button.css('opacity', 'unset');
                });
                $("button[type='submit']").on('click', self._onSubmit.bind(self));
            });
        },

        _formValidate: function ($form) {
            $form.addClass('was-validated');
            return $form[0].checkValidity();
        },

        _formValidateGetValues: function () {
            var post = {
                'profile_description': $('textarea[name="profile_description"]').val(),
            };
            return post;
        },

        _onSubmit: function (ev) {
            ev.preventDefault();
            ev.stopPropagation();
            var self = this;
            var $target = $(ev.currentTarget);
            var $form = $target.closest('form');

            if (this._formValidate($form)) {
                var post = this._formValidateGetValues(); 
                $form.css('pointer-events', 'none');
                $form.find('button').css('opacity', 0.65);

                return this._rpc({
                        route: $form.attr('action'),
                        params: post,
                    })
                    .then(function (result) {
                        if(result){
                            window.location.reload();
                        }
                    });
            }
        },
    });

    publicWidget.registry.ProfileDesc = publicWidget.Widget.extend({
        selector: '#o_wprofile_desc_edit_form',

        start: function () {
            var def = this._super.apply(this, arguments);
            var getDetailModal = new ProfileDescForm(this);
            return Promise.all([def, getDetailModal.attachTo(this.$el)]);
        },
    });
    // #endregion

    return {
        ProfileEditDialog: ProfileEditDialog,
        websiteProfileEdit: publicWidget.registry.websiteProfileEdit
    };

});