# -*- coding: utf-8 -*-
{
    'name': "Dobtor User Profile",

    'summary': """
        User profile in front end""",

    'description': """
        Website User Profile
    """,

    'author': "Dobtor SI",
    'website': "http://www.dobtor.com",
    'category': 'Website/Website',
    'version': '0.1',
    'depends': [
        'base',
        'website',
        'dobtor_user_signup',
        'dobtor_partner_group_extend',
        'dobtor_user_apps',
        'dobtor_user_contact_info',
    ],

    'data': [
        # 'security/ir.model.access.csv',
        'data/app_launcher_data.xml',
        'data/profile_email_verify_data.xml',
        'data/fields_show_distinction.xml',
        'views/assets.xml',
        'views/res_config_settings_views.xml',
        'views/res_partner_views.xml',
        'views/profile_header_widget.xml',
        'views/profile_content_widget.xml',
        'views/templates.xml',
        'views/my_member_templates.xml',
        'views/profile_modal_templates.xml',
    ],
}
