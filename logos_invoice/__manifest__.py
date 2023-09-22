# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": "Logos_Invoice",
    "version": "1.0",
    "author": "ADHOC SA - wsf",
    'category': 'Accounting/Localizations',
    "summary": "LATAM Document Types",
    'description': """
Mósudo para Logos 

""",
    "depends": [
        'l10n_latam_invoice_document', 'sale'
    ],
    "data": [
        'views/account_journal_view.xml',
        'views/crm_team_views.xml',
        'report/report_invoice.xml',
        'report/sale_report_templates.xml',
        #'report/sale_report_templates2.xml',
        'report/sale_report.xml',
        'report/2/report_invoice_fe.xml',

        #'security/ir.model.access.csv',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
