# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle 
#
##############################################################################

from odoo import models, fields, api, _


class hr_expense_sheet(models.Model):
    _inherit = 'hr.expense.sheet'

    exp_number = fields.Char('Number', default='/', required="1")
    
    
    @api.model
    def create(self, vals):
        if vals.get('exp_number', '/') == '/':
            vals['exp_number'] = self.env['ir.sequence'].next_by_code(
                'hr.expense.sheet') or '/'
        return super(hr_expense_sheet, self).create(vals)
        
    def copy(self, default=None):
        if default is None:
            default = {}
        default['exp_number'] = '/'
        return super(hr_expense_sheet, self).copy(default=default)
        
    def action_sheet_move_create(self):
        res = super(hr_expense_sheet,self).action_sheet_move_create()
        if self.account_move_id:
            self.account_move_id.ref = '['+ str(self.exp_number) + '] '+ str(self.name)
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
