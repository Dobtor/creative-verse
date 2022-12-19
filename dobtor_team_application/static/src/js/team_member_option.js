odoo.define('dobtor_team_application.team_member_option', function (require) {
    'use strict';

    const core = require('web.core');
    const request_common = require('dobtor_request_application.request_common');
    const team_member = require('dobtor_team.team_member_option');
    const _t = core._t;

    team_member.TeamMemberOptions.include({
        xmlDependencies: (team_member.TeamMemberOptions.prototype.xmlDependencies || []).concat(
            [
                '/dobtor_team_application/static/src/xml/kick_modal.xml',
            ]
        ),
        // TODO : 預留 js file, 目前採用罐頭文無需此檔案, 但如果流程變更需要填寫事由, 則需要實作該檔案
    });

});