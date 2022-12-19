# -*- coding: utf-8 -*-
{
    'name': "Dobtor Team",
    'summary': """
        群組 - 專案小組
    """,
    'description': """
        群組 - 專案小組
            - 用戶申請加入
    """,
    'author': "Dobtor SI",
    'website': "https://www.dobtor.com",
    'category': 'Team',
    'version': '0.1',
    'depends': [
        'base',
        'mail',
        'dobtor_user_profile'
    ],
    'data': [
        'security/res_group.xml',
        'security/ir.model.access.csv',
        'data/website_data.xml',
        "data/mail_template_data.xml",
        'data/fields_show_distinction.xml',
        'data/team_email_verify_data.xml',
        'views/assets.xml',
        'views/team_profile_templates.xml',
        'views/res_partner_views.xml',
        'views/team_common_templates.xml',
        'views/my_member_templates.xml',
        'views/team_modal_templates.xml',
        'views/team_home_templates.xml',
        'views/team_management_views.xml',
        'views/profile_content_widget.xml',
    ],
    'application': True,
}
