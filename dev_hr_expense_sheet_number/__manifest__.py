# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

{
    'name': 'Hr Expense sheet Uniq Number, Expense Number',
    'version': '1.0',
    'sequence': 1,
    'category': 'Generic Modules/Human Resources',
    'description':
        """
  odoo app will add unique number for each hr expense sheet'

Hr expense sheet number
Odoo Hr expense sheet number
This apps will help to generate unique number for hr expense sheet sheet
Odoo This apps will help to generate unique number for hr expense sheet
HR expense 
Odoo HR Expense 
Manage HR expense 
Odoo manage HR expense 
HR expense sheet 
Odoo HR expense sheet 
Manage HR expense sheet 
Odoo manage HR expense sheet 
Generate Unique number for hr expense sheet
Odoo Generate Unique number for hr expense sheet
Number will pass to Journal Entry
Odoo Number will pass to Journal Entry
Number include current year and month
Odoo Number include current year and month
Create HR Expense Sheet
Odoo Create HR Expense Sheet

odoo app will add unique number for each hr expense sheet,unique number, unique expense sheet number, expense number, expense sequence,manage HR expense sheet,Unique number for hr expense sheet,Hr expense sheet number, expense uniq sequence


    """,
    'summary': 'odoo app will add unique number for each hr expense sheet,unique number, unique expense sheet number, expense number, expense sequence,manage HR expense sheet,Unique number for hr expense sheet,Hr expense sheet number, expense uniq sequence',
    'depends': ['hr_expense'],
    'data': [
        'views/ir_sequence_data.xml',
        'views/hr_expense_sheet_views.xml',
        ],
    'demo': [],
    'test': [],
    'css': [],
    'qweb': [],
    'js': [],
    'images': ['images/main_screenshot.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    
    #author and support Details
    'author': 'DevIntelle Consulting Service Pvt.Ltd',
    'website': 'http://www.devintellecs.com',    
    'maintainer': 'DevIntelle Consulting Service Pvt.Ltd', 
    'support': 'devintelle@gmail.com',
    'price':8.0,
    'currency':'EUR',
    #'live_test_url':'https://youtu.be/A5kEBboAh_k',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
