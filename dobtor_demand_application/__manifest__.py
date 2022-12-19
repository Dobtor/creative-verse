# -*- coding: utf-8 -*-
{
    'name': "Dobtor Demand Application",

    'summary': """
        - 管理者拒絕需求申請時，留言填寫拒絕原因，並通知需求申請者
        - 需求者放棄需求申請時，留言填寫拒絕原因，並通知需求申請者
        - 需求者拒絕服務申請時，留言填寫拒絕原因，並通知服務報名者
        - 管理者拒絕服務申請時，留言填寫拒絕原因，並通知服務報名者
    """,

    'description': """
        Dobtor Demand Application
    """,

    'author': "Dobtor SI",
    'website': "https://www.dobtor.com",
    'category': 'website',
    'version': '0.1',
	
    'depends': [
		'dobtor_request_application',
        'dobtor_team_application',
        'dobtor_demand_marketplace',
	],

    'data': [
        # 'security/ir.model.access.csv',
        'data/data.xml',
        'views/assets.xml',
    ],
	'application': True,
}
