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
from odoo.exceptions import ValidationError


class employee_loan_type(models.Model):
    _name = 'employee.loan.type'
    _description = 'Type of employee Loan'
    

    def _compute_loan_done(self):
        for record in self:
            emp_loan = self.env['employee.loan'].search([('state','=','done'),('loan_type_id','=',record.id)])
            record.count_loan_done = len(emp_loan)
            
    def _compute_loan_paid(self):
        for record in self:
            emp_loan = self.env['employee.loan'].search([('state','=','paid'),('loan_type_id','=',record.id)])
            record.count_loan_paid = len(emp_loan)
            
    def _compute_loan_draft(self):
        for record in self:
            emp_loan = self.env['employee.loan'].search([('state','=','draft'),('loan_type_id','=',record.id)])
            record.count_loan_draft = len(emp_loan)


    name = fields.Char('Name', required="1")
    loan_limit = fields.Float('Loan Amount Limit', default=50000, required="1")
    loan_term = fields.Integer('Loan Term', default=12, required="1")
    is_apply_interest = fields.Boolean('Apply Interest')
    interest_rate = fields.Float('Interest Rate',default=10)
    interest_type = fields.Selection([('liner','Liner'),('reduce','Reduce')],string='Interest Type',
                                     default='liner')
                                     
    loan_account = fields.Many2one('account.account',string='Loan Account',required="1")
    interest_account = fields.Many2one('account.account',string='Interest Account', required="1")
    journal_id = fields.Many2one('account.journal',string='Journal', required="1")
    color = fields.Integer(string= 'Color')
    count_loan_draft = fields.Integer(compute='_compute_loan_draft')
    count_loan_done = fields.Integer(compute='_compute_loan_done')
    count_loan_paid = fields.Integer(compute='_compute_loan_paid')
    priority = fields.Selection([('0','Low'),('1','Normal')],default='0')
    
    def _get_action(self, action_xmlid):
        # TDE TODO check to have one view + custo in methods
        action = self.env.ref(action_xmlid).read()[0]
        if self:
            action['display_name'] = self.display_name
        return action

    def get_action_loan_tree_done(self):
        return self._get_action('dev_hr_loan.action_loan_tree_done')
    
    def get_action_loan_tree_draft(self):
        return self._get_action('dev_hr_loan.action_loan_tree_draft')
    
    def action_get_hr_loan_type(self):
        return self._get_action('dev_hr_loan.get_hr_loan_type')
    def get_action_loan_paid(self):
        return self._get_action('dev_hr_loan.action_loan_paid')
    def get_action_hr_approval(self):
        return self._get_action('dev_hr_loan.action_hr_approval')
    
    def get_loan_create(self):
        return self._get_action('dev_hr_loan.action_loan_create')
    def get_all_loan(self):
        return self._get_action('dev_hr_loan.action_view_all_loan')
    def get_setting(self):
        return self._get_action('dev_hr_loan.action_setting')


    @api.constrains('is_apply_interest','interest_rate','interest_type')
    def _check_interest_rate(self):
        for loan in self:
            if loan.is_apply_interest:
                if loan.interest_rate <= 0:
                    raise ValidationError("Interest Rate must be greater 0.00")
                if not loan.interest_type:
                    raise ValidationError("Please Select Interest Type")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
