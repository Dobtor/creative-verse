# -*- coding: utf-8 -*-
{
    'name': "Dobtor Team Application",

    'summary': """
        群組功能申請模組
    """,

    'description': """
        群組發布請求(Publish)
        群組開活動審核(Organizer能不能被選)
        群組發需求(Organizer能不能被選)
    """,

    'author': "Dobtor SI",
    'website': "https://www.dobtor.com",
    'category': 'Web',
    'version': '14.0',
	
    'depends': [
        'dobtor_request_application',
        'dobtor_team',
	],

    'data': [
        # security
        # data
        'data/data.xml',
        # views
        'views/assets.xml',
        'views/team_management_views.xml',
        'views/team_profile_template.xml',      
        'views/my_member_templates.xml',
    ],
	'application': True,
}
