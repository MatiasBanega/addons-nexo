# -*- coding: utf-8 -*-
{
    'name': 'Payment internal transfer',
    "author": "Younis",
    'version': '15.0.0.01',
    'summary': "Payment Journal to Account transfer payment Account to Journal transfer internal account transfer internal transfer payment  Account Payment Voucher payment account transfer payment account to account to transfer account cash transfer bank account transfer",
    'description': """ This app helps user to transfer payment internally with many options like account to account, journal to account, and account to journal. 
    """,
    "license" : "OPL-1",
    'depends': ['base','sale_management','account','purchase','stock_account'],
    'data': [
        'views/inherit_payment.xml',
    ],
    'installable': True,
    'auto_install': False,
    'price': 18,
    'currency': "EUR",
    'category': 'Accounting',

}

