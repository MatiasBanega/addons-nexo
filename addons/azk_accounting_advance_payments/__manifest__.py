{
    'name': "AZK Accounting Advance Payments",
    'author': "Azkatech SAL",
    'website': "http://www.azka.tech",
    'category': 'appraisal',
    'version': '15.0.0.0.0',
    'license': "AGPL-3",
    'support': "support+odoo@azka.tech",
    'depends': ['base', 
                'sale_management', 
                'purchase', 
                'contacts', 
                'account_accountant',
                ],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order.xml',
        'views/sale_payment_history.xml',
        'views/purchase_order.xml',
        'views/purchase_payment_history.xml',
        'views/account_payment.xml',
        'views/account_move.xml',
        'views/res_partner.xml',
        'wizard/advance_payment_wizard.xml',
    ],
    'images' : ['images/static/description/banner.png'],

}