{
    "name": "Project Description",
    "summary": "Add a description to projects",
    "version": "1.1.3",
    "category": "Project",
    "website": "https://github.com/OCA/project",
    "author": "Tecnativa, " "C2i Change 2 improve, " "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "hr",
        "project",
        "sale_timesheet",
        "product",
        "stock",
        "sale_stock",
        "project_category",
        "purchase",
        "account_accountant",
        # "phl_project_team",
        # "project_project_category",
    ],
    "data": [
        "security/ir.model.access.csv",
        # "views/project_task_views.xml",
        # 'views/project_project_category_view.xml',
        # 'views/project_task_views.xml',
        # 'views/project_project_view.xml',


    # active down

        # "data/project_data.xml",
        "data/task_mail_template.xml",
        # "data/task_cron_data.xml",
        "wizard/schedule_item_import_view.xml",
        "views/project_view.xml",
        "views/port_view.xml",
        "views/project_schedule_items_view.xml",
        "views/product_template.xml",
        "views/sale_order_view.xml",
        "views/project_type_view_ext.xml",
        "views/purchase_order_view.xml",
        "views/account_move.xml",

    ],
    "installable": True,
}
