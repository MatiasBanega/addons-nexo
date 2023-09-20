# -*- coding: utf-8 -*-
{
    "name": "Dropbox Odoo Integration",
    "version": "15.0.3.0.1",
    "category": "Document Management",
    "author": "faOtools",
    "website": "https://faotools.com/apps/15.0/dropbox-odoo-integration-644",
    "license": "Other proprietary",
    "application": True,
    "installable": True,
    "auto_install": False,
    "depends": [
        "cloud_base"
    ],
    "data": [
        "data/data.xml",
        "security/ir.model.access.csv",
        "views/clouds_client.xml"
    ],
    "qweb": [
        
    ],
    "assets": {},
    "external_dependencies": {
        "python": [
                "dropbox"
        ]
},
    "summary": "The tool to automatically synchronize Odoo attachments with DropBox files in both ways",
    "description": """
For the full details look at static/description/index.html

* Features * 

- How synchronization works
- Dropbox URLs



#odootools_proprietary

    """,
    "images": [
        "static/description/main.png"
    ],
    "price": "149.0",
    "currency": "EUR",
    "live_test_url": "https://faotools.com/my/tickets/newticket?&url_app_id=18&ticket_version=15.0&url_type_id=3",
}