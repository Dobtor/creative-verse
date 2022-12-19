# -*- coding: utf-8 -*-
{
    'name': "dobtor_demand_marketplace",

    'summary': """
        用戶
            前台用戶可以在參加的群組建立需求提交申請
            用戶提交需求需要預扣時間點數
            用戶可以管理已經發佈的需求/下架
            用戶可以管理已登錄的服務/接受服務/取消服務＋通知

        群組
            時間點數不足的申請可以由群組錢包代扣 (特例)
            審核成員提出的需求申請
            審核成員登錄的服務
    """,

    'description': """
        Dobtor Demand Marketplace
    """,

    'author': "Dobtor SI",
    'website': "https://www.dobtor.com",
    'category': 'website',
    'version': '0.1',
	
    'depends': [
		'base',
        'dobtor_demand',
        'dobtor_user_wallet',
        'dobtor_event_team',
	],

    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/mail_template_data.xml',
        'data/app_data.xml',
        'data/app_launcher_service.xml',
        'views/assets.xml',
        'views/sale_order_views.xml',
        'views/event_demand_views.xml',
        'views/event_registrantion_views.xml',
        'views/team_common_templates.xml',
        # TODO: (待實作)群組需求統計改為書籤顯示，這邊還有內容排版開發
        # 'views/team_profile_templates.xml',
        'views/team_demand_templates.xml',
        'views/team_demand_report_templates.xml',
        'views/my_demand_templates.xml',
        'views/my_service_templates.xml',
        'views/service_audit_templates.xml',
        'views/demand_description_template.xml',
        'views/demand_templates.xml',
    ],
	'application': True,
}
