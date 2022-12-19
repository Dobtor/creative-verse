odoo.define('dobtor_user_profile.profile_user_area_edit', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var wysiwygLoader = require('web_editor.loader');
    var core = require('web.core');
    var _t = core._t;
    var qweb = core.qweb;


    publicWidget.registry.profileUserAreaEdit = publicWidget.Widget.extend({
        selector: '#user_about_block',
        events: {
            'click .o_wprofile_about_js_edit': '_onEditClick',
            'click .o_wprofile_about_edit_submit_btn': '_SaveClick', 
            'click .o_wprofile_about_edit_js_cancel': '_CancelClick',
        },

        start: function () {
            this.slug = this.$el.data('slug');
            this.$container = this.$target;
            return this._super.apply(this, arguments);
        },
    
        _onEditClick: function (ev) {
            ev.preventDefault();
            var self = this;
            var $button = $(ev.currentTarget);
            $button.css('pointer-events', 'none');
            $button.css('opacity', 0.65);

            return this._rpc({
                route: '/profile/' + this.slug + '/about/edit/template',
                params: { about_edit: true },
            }).then(function (result) {
                self.$container.html("<form id='user_about_edit_form'><input type='hidden' name='csrf_token' value='" + odoo.csrf_token + "'/>" + result + "</form>");
                self._render_editor(self.$container.find('textarea.o_wysiwyg_loader'));
            });
        },

        _render_editor: function($textarea) {
            var self = this;
            var toolbar = [
                ['style', ['style']],
                ['font', ['bold', 'italic', 'underline', 'clear']],
                ['para', ['ul', 'ol', 'paragraph']],
                ['table', ['table']],
                ['insert', ['link', 'picture']],
                ['view', ['codeview']],
                ['history', ['undo', 'redo']],
            ];

            wysiwygLoader.load(self, $textarea[0], {
                height: 200,
                minHeight: 80,
                toolbar: toolbar,
                styleWithSpan: false,
                disableFullMediaDialog: true,
                disableResizeImage: true,
            }).then(wysiwyg => {
                self._wysiwyg = wysiwyg;
            });
        },

        _disabled_btn: function() {
            this.$container.find('button').css('pointer-events', 'none');
            this.$container.find('button').css('opacity', 0.65);
        },

        _SaveClick: function (ev) {
            var self = this;
            ev.preventDefault();
            this._disabled_btn();

            if (this._wysiwyg) {
                this._wysiwyg.save();
            }
            return this._rpc({
                route: '/profile/' + this.slug + '/about/edit',
                params: {'profile_content': this.$container.find('#profile_content').val()},
            }).then(function (result) {
                if (result)
                    window.location.reload();
            });
        },

        _CancelClick: function (ev) {
            var self = this;
            ev.preventDefault();
            this._disabled_btn();

            return this._rpc({
                route: '/profile/' + this.slug + '/about/edit/template',
                params: {},
            }).then(function (result) {
                self.$container.html(result);
            });
        },
    });

    return {
        profileUserAreaEdit: publicWidget.registry.profileUserAreaEdit,
    };

});