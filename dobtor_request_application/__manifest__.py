# -*- coding: utf-8 -*-
{
    'name': "Dobtor Request Application",

    'summary': """
        請求申請.審核模組
    """,

    'description': """
        提供後台User簡易管理請求.審核功能之核心模組
    """,

    'author': "Dobtor SI",
    'website': "https://www.dobtor.com",
    'category': 'Web',
    'version': '14.0',
	
    'depends': [
        'base',
		'web',
        'mail',
	],

    'data': [
        # security
        'security/res_group.xml',
        'security/ir.model.access.csv',
        # data
        'data/mail_template_data.xml',
        # wizard 
        'wizard/request_reject.xml',
        # views
        'views/assets.xml',
        'views/web_assets.xml',
        'views/res_partner_view.xml',
        'views/request_application_views.xml',
        'views/menuitem.xml',
    ],
	'application': True,
}
