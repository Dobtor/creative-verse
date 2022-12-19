# -*- coding: utf-8 -*-
{
    'name': "dobtor_demand",

    'summary': """
        服務交換系統
    """,

    'description': """
        提供用戶提出需求, 或是給予服務的交換系統
    """,

    'author': "Dobtor SI",
    'website': "https://www.dobtor.com",
    'category': 'Uncategorized',
    'version': '0.1',
	
    'depends': [
		'dobtor_event',
        'purchase',
	],

    'data': [
        'security/ir.model.access.csv',
        'data/website_data.xml',
        'data/mail_template_data.xml',
        'data/app_launcher_demand.xml',
        'views/assets.xml',
        # View
        'views/event_demand_views.xml',
        'views/event_demand_tag_views.xml',
        'views/event_registrantion_views.xml',
        'views/purchase_order_views.xml',
        'views/menuitem.xml',
        'wizard/demand_configurator_views.xml',
        'wizard/demand_edit_registration.xml',
        # Template
        'views/demand_template.xml',
        'views/demand_description_template.xml',
        'views/my_demand_templates.xml',
    ],
	'application': True,
}
