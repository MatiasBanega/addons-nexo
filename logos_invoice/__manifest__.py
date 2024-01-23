{
    "name": "Logos_Invoice",
    "version": "1.0",
    "author": "DEVMAN",
    "category": "Accounting/Localizations",
    "summary": "LATAM Document Types",
    "description": """
Módulo para Logos en presupuestos y facturas de acuerdo al equipo de ventas y el diario de facturación 

""",
    "depends": ["l10n_latam_invoice_document", "sale"],
    "data": [
        "report/report.xml",
        "report/report_sale_order.xml", 
        "report/2/report_invoice_fe.xml",
        "report/2/report_inherit_sale_order_document.xml",

        "views/account_journal_view.xml",
        "views/crm_team_views.xml",
    ],
    "installable": True,
    "license": "LGPL-3",
}
