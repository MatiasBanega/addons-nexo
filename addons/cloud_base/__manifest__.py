# -*- coding: utf-8 -*-
{
    "name": "Cloud Storage Solutions",
    "version": "15.0.1.2.5",
    "category": "Document Management",
    "author": "faOtools",
    "website": "https://faotools.com/apps/15.0/cloud-storage-solutions-640",
    "license": "Other proprietary",
    "application": True,
    "installable": True,
    "auto_install": False,
    "depends": [
        "mail"
    ],
    "data": [
        "data/data.xml",
        "data/cron.xml",
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/clouds_log.xml",
        "views/sync_model.xml",
        "views/clouds_client.xml",
        "views/ir_attachment.xml",
        "views/clouds_folder.xml",
        "views/clouds_queue.xml",
        "views/res_config_settings.xml",
        "wizard/mass_attachment_update.xml",
        "views/menu.xml",
        "views/templates.xml"
    ],
    "assets": {
        "web.assets_backend": [
                "cloud_base/static/src/components/cloud_folder_tree/cloud_folder_tree.js",
                "cloud_base/static/src/js/no_archive_controller.js",
                "cloud_base/static/src/js/no_archive_view.js",
                "cloud_base/static/src/js/jstree_widget.js",
                "cloud_base/static/src/js/parent_many2one.js",
                "cloud_base/static/src/models/attachment/attachment.js",
                "cloud_base/static/src/models/attachment_list/attachment_list.js",
                "cloud_base/static/src/models/attachment_card/attachment_card.js",
                "cloud_base/static/src/models/thread/thread.js",
                "cloud_base/static/src/components/attachment_box/attachment_box.js",
                "cloud_base/static/src/css/file_manager.css",
                "cloud_base/static/src/js/file_manager_kanbancontroller.js",
                "cloud_base/static/src/js/file_manager_kanbanmodel.js",
                "cloud_base/static/src/js/file_manager_kanbanrecord.js",
                "cloud_base/static/src/js/file_manager_kanbanrenderer.js",
                "cloud_base/static/src/js/file_manager_kanbanview.js",
                "cloud_base/static/src/js/cloud_logs.js"
        ],
        "web.assets_qweb": [
                "cloud_base/static/src/xml/*.xml",
                "cloud_base/static/src/components/cloud_folder_tree/cloud_folder_tree.xml",
                "cloud_base/static/src/components/attachment_card/attachment_card.xml",
                "cloud_base/static/src/components/attachment_box/attachment_box.xml"
        ]
},
    "demo": [
        
    ],
    "external_dependencies": {
        "python": [
                "sortedcontainers"
        ]
},
    "summary": "The tool to flexibly structure Odoo attachments in folders and synchronize directories with cloud clients: Google Drive, OneDrive / SharePoint, Nextcloud / ownCloud, Dropbox",
    "description": """
For the full details look at static/description/index.html

* Features * 

- Odoo File Manager Interface
- Enhanced attachment box 
- Cloud storage synchronization
- &lt;span id=&quot;cloud_base_folder_rules&quot;&gt;Automatic folders' structure&lt;/span&gt;
- File manager and sync access rights
- Use notes



#odootools_proprietary

    """,
    "images": [
        "static/description/main.png"
    ],
    "price": "245.0",
    "currency": "EUR",
    "live_test_url": "https://faotools.com/my/tickets/newticket?&url_app_id=11&ticket_version=15.0&url_type_id=3",
}