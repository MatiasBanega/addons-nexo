{
    "name": "Stock Vendor Evaluation",
    "summary": """
        Rate each receipt and analyze vendor ratings.
    """,
    "author": "Mint System GmbH, Odoo Community Association (OCA)",
    "website": "https://www.mint-system.ch",
    "category": "Inventory",
    "version": "15.0.1.1.1",
    "license": "AGPL-3",
    "depends": ["purchase_stock", "contacts"],
    "data": [
        "security/ir.model.access.csv",
        "views/views.xml",
        "views/view_picking_form.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
