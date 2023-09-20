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
from datetime import datetime
from dateutil.relativedelta import relativedelta


class employee_loan(models.Model):
    _name = 'employee.loan'
    _description = 'Loan of an Employee'
    _inherit = 'mail.thread'
    _order = 'name desc'

    loan_state=[('draft','Draft'),
                ('request','Submit Request'),
                ('dep_approval','Department Approval'),
                ('hr_approval','HR Approval'),
                ('paid','Paid'),
                ('done','Done'),
                ('close', 'Close'),
                ('reject','Reject'),
                ('cancel','Cancel')]
                
    @api.model
    def _get_employee(self):
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
        return employee_id

    @api.model
    def _get_default_user(self):
        return self.env.user

    def send_loan_detail(self):
        if self.employee_id and self.employee_id.work_email:
            template_id = self.env['ir.model.data'].get_object_reference('dev_hr_loan',
                                                             'dev_employee_loan_detail_send_mail')

            template_id = self.env['mail.template'].browse(template_id[1])
            template_id.send_mail(self.ids[0], True)
        return True
        
    @api.depends('start_date','term')
    def _get_end_date(self):
        for loan in self:
            end_date = False
            if loan.start_date and loan.term:
                start_date =  self.start_date
                end_date = start_date+relativedelta(months=self.term)
            loan.end_date = end_date

    @api.depends('installment_lines','paid_amount')
    def get_extra_interest(self):
        for loan in self:
            amount = 0
            for installment in loan.installment_lines:
                if installment.is_skip:
                    amount += installment.ins_interest
            loan.extra_in_amount = amount

    name = fields.Char('Name',default='/',copy=False)
    state = fields.Selection(loan_state,string='State',default='draft', track_visibility='onchange')
    employee_id = fields.Many2one('hr.employee',default=_get_employee, required="1")
    department_id = fields.Many2one('hr.department',string='Department')
    hr_manager_id = fields.Many2one('hr.employee',string='Hr Manager')
    manager_id = fields.Many2one('hr.employee',string='Department Manager', required="1")
    job_id = fields.Many2one('hr.job',string="Job Position")
    date = fields.Date('Date',default=fields.Date.today())
    start_date = fields.Date('Start Date',default=fields.Date.today(),required="1")
    end_date = fields.Date('End Date',compute='_get_end_date')
    term = fields.Integer('Term',required="1")
    loan_type_id = fields.Many2one('employee.loan.type',string='Type',required="1")
    payment_method = fields.Selection([('by_payslip','By Payslip')],string='Payment Method',default='by_payslip', required="1")
    loan_amount = fields.Float('Loan Amount',required="1")
    paid_amount = fields.Float('Paid Amount',compute='get_paid_amount')
    remaing_amount = fields.Float('Remaing Amount', compute='get_remaing_amount')
    installment_amount = fields.Float('Installment Amount',required="1", compute='get_installment_amount')
    loan_url = fields.Char('URL', compute='get_loan_url')
    user_id = fields.Many2one('res.users',default=_get_default_user)
    is_apply_interest = fields.Boolean('Apply Interest')
    interest_type = fields.Selection([('liner', 'Liner'), ('reduce', 'Reduce')], string='Interest Type')
    interest_rate = fields.Float(string='Interest Rate')
    interest_amount = fields.Float('Interest Amount', compute='get_interest_amount')
    installment_lines = fields.One2many('installment.line','loan_id',string='Installments',)
    notes = fields.Text('Reason', required="1")
    is_close = fields.Boolean('IS close',compute='is_ready_to_close')
    move_id = fields.Many2one('account.move',string='Journal Entry')
    loan_document_line_ids = fields.One2many('dev.loan.document','loan_id')
    installment_count = fields.Integer(compute='get_interest_count')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    # extra field from v12 module
    n_paid_amount = fields.Float(related='paid_amount', string='Paid Amount', store=True)
    extra_in_amount = fields.Float('Extra Int. Amount', compute='get_extra_interest')
    n_extra_in_amount = fields.Float(related='extra_in_amount', string='Extra Interest Amount', store=True)
    n_interest_amount = fields.Float(related='interest_amount', string='Interest Amount', store=True)
    n_remaing_amount = fields.Float(related='remaing_amount', string='Remaining Amount', store=True)

    @api.depends('installment_lines')
    def get_interest_count(self):
        for loan in self:
            count = 0
            if loan.installment_lines:
                count = len(loan.installment_lines)
            loan.installment_count = count

    @api.onchange('term','interest_rate','interest_type')
    def onchange_term_interest_type(self):
        if self.loan_type_id:
            self.term = self.loan_type_id.loan_term
            self.interest_rate = self.loan_type_id.interest_rate
            self.interest_type = self.loan_type_id.interest_type
    
    @api.depends('remaing_amount')
    def is_ready_to_close(self):
        for loan in self:
            ready = False
            if loan.remaing_amount <= 0 and loan.state == 'done':
                ready = True
            loan.is_close = ready

    @api.depends('installment_lines')
    def get_paid_amount(self):
        for loan in self:
            amt = 0
            for line in loan.installment_lines:
                if line.is_paid:
                    if line.is_skip:
                        amt += line.ins_interest
                    else:
                        amt += line.total_installment
            loan.paid_amount = amt




    def compute_installment(self):
        vals=[]
        for i in range(0,self.term):
            date = self.start_date
            date = date+relativedelta(months=i)
            amount = self.loan_amount
            interest_amount = 0.0
            ins_interest_amount=0.0
            if self.is_apply_interest:
                amount = self.loan_amount
                interest_amount = (amount * self.term/12 * self.interest_rate)/100

                if self.interest_rate and self.loan_amount and self.interest_type == 'reduce':
                    amount = self.loan_amount - self.installment_amount * i
                    interest_amount = (amount * self.term / 12 * self.interest_rate) / 100
                ins_interest_amount = interest_amount / self.term
            vals.append((0, 0,{
                'name':'INS - '+self.name+ ' - '+str(i+1),
                'employee_id':self.employee_id and self.employee_id.id or False,
                'date':date,
                'amount':amount,
                'interest':interest_amount,
                'installment_amt':self.installment_amount,
                'ins_interest':ins_interest_amount,
            }))
        if self.installment_lines:
            for l in self.installment_lines:
                l.unlink()
        self.installment_lines=vals

    @api.depends('paid_amount','loan_amount','interest_amount')
    def get_remaing_amount(self):
        for loan in self:
            remaining = (loan.loan_amount + loan.interest_amount) - loan.paid_amount
            loan.remaing_amount = remaining

    @api.depends('loan_amount','interest_rate','is_apply_interest')
    def get_interest_amount(self):
        for loan in self:
            amt = 0.0
            if loan.is_apply_interest:
                if loan.interest_rate and loan.loan_amount and loan.interest_type == 'liner':
                    loan.interest_amount = (loan.loan_amount * loan.term/12 * loan.interest_rate)/100
                if loan.interest_rate and loan.loan_amount and loan.interest_type == 'reduce':
                    loan.interest_amount = (loan.remaing_amount * loan.term/12 * loan.interest_rate)/100
                    for line in loan.installment_lines:
                        amt += line.ins_interest
            loan.interest_amount = amt


    # @api.depends('interest_amount')
    # def get_install_interest_amount(self):
    #     for loan in self:
    #         if loan.is_apply_interest:
    #             if loan.interest_amount and loan.term:
    #                 loan.ins_interest_amount = loan.interest_amount / loan.term

    @api.onchange('interest_type','interest_rate')
    def onchange_interest_rate_type(self):
        if self.interest_type and self.is_apply_interest:
            if self.interest_rate != self.loan_type_id.interest_rate:
                self.interest_rate = self.loan_type_id.interest_rate
            if self.interest_type != self.loan_type_id.interest_type:
                self.interest_type = self.loan_type_id.interest_type

    def get_loan_url(self):
        for loan in self:
            ir_param = self.env['ir.config_parameter'].sudo()
            base_url = ir_param.get_param('web.base.url')
            action_id = self.env.ref('dev_hr_loan.action_employee_loan').id
            menu_id = self.env.ref('dev_hr_loan.menu_employee_loan').id
            if base_url:
                base_url += '/web#id=%s&action=%s&model=%s&view_type=form&cids=&menu_id=%s' % (loan.id, action_id, 'employee.loan', menu_id)
            loan.loan_url = base_url

    @api.depends('term','loan_amount')
    def get_installment_amount(self):
        amount = 0
        for loan in self:
            if loan.loan_amount and loan.term:
                amount = loan.loan_amount / loan.term
            loan.installment_amount = amount


    @api.constrains('employee_id')
    def _check_loan(self):
        now = datetime.now()
        year = now.year
        s_date = str(year)+'-01-01'
        e_date = str(year)+'-12-01'
        
        loan_ids = self.search([('employee_id','=',self.employee_id.id),('date','<=',e_date),('date','>=',s_date)])
        loan = len(loan_ids)
        if loan > self.employee_id.loan_request:
            raise ValidationError("You can create maximum %s loan" % self.employee_id.loan_request)
            

        
    

    @api.constrains('loan_amount','term','loan_type_id','employee_id.loan_request')
    def _check_loan_amount_term(self):
        for loan in self:
            if loan.loan_amount <= 0:
                raise ValidationError("Loan Amount must be greater 0.00")
            elif loan.loan_amount > loan.loan_type_id.loan_limit:
                raise ValidationError("Your can apply only %s amount loan" % loan.loan_type_id.loan_limit)

            if loan.term <= 0:
                raise ValidationError("Loan Term must be greater 0.00")
            elif loan.term > loan.loan_type_id.loan_term:
                raise ValidationError("Loan Term Limit for Your loan is %s months" % loan.loan_type_id.loan_term)



    @api.onchange('loan_type_id')
    def _onchange_loan_type(self):
        if self.loan_type_id:
            self.term = self.loan_type_id.loan_term
            self.is_apply_interest = self.loan_type_id.is_apply_interest
            if self.is_apply_interest:
                self.interest_rate = self.loan_type_id.interest_rate
                self.interest_type = self.loan_type_id.interest_type




    
    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            self.department_id = self.employee_id and self.employee_id.department_id and \
                                 self.employee_id.department_id.id or False,

            self.manager_id = self.department_id and self.department_id.manager_id and \
                                  self.department_id.manager_id.id or self.employee_id.parent_id.id or False,

            self.job_id = self.employee_id.job_id and self.employee_id.job_id.id or False,

    def action_send_request(self):
        if not self.manager_id:
            raise ValidationError(_('Please Select Department manager'))
        
        self.state = 'request'
        if not self.installment_lines:
            self.compute_installment()
        if self.manager_id and self.manager_id.work_email:
            ir_model_data = self.env['ir.model.data']
            template_id = ir_model_data._xmlid_lookup('dev_hr_loan.dev_dep_manager_request')[2]
            mtp = self.env['mail.template']
            template_id = mtp.browse(template_id)
            template_id.write({'email_to': self.manager_id.work_email})
            template_id.send_mail(self.ids[0], True)
            


    def get_hr_manager_email(self):
        group_id = self.env['ir.model.data']._xmlid_lookup('hr.group_hr_manager')[2]
        group_ids = self.env['res.groups'].browse(group_id)
        email=''
        if group_ids:
            employee_ids = self.env['hr.employee'].search([('user_id', 'in', group_ids.users.ids)])
            for emp in employee_ids:
                if email:
                    email = email+','+emp.work_email
                else:
                    email= emp.work_email
        return email

    def dep_manager_approval_loan(self):
        self.state = 'dep_approval'
        email = self.get_hr_manager_email()
        if email:
            ir_model_data = self.env['ir.model.data']
            template_id = ir_model_data._xmlid_lookup('dev_hr_loan.dev_hr_manager_request')[2]
            mtp = self.env['mail.template']
            template_id = mtp.browse(template_id)
            template_id.write({'email_to': email})
            template_id.send_mail(self.ids[0], True)

    def hr_manager_approval_loan(self):
        self.state = 'hr_approval'
        employee_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)],limit=1)
        self.hr_manager_id = employee_id and employee_id.id or False
        if self.employee_id.work_email and self.hr_manager_id:
            ir_model_data = self.env['ir.model.data']
            template_id = ir_model_data._xmlid_lookup('dev_hr_loan.hr_manager_confirm_loan')[2]
            mtp = self.env['mail.template']
            template_id = mtp.browse(template_id)
            template_id.write({'email_to': self.employee_id.work_email})
            template_id.send_mail(self.ids[0], True)

    def dep_manager_reject_loan(self):
        self.state = 'reject'
        if self.employee_id.work_email:
            ir_model_data = self.env['ir.model.data']
            template_id = ir_model_data._xmlid_lookup('dev_hr_loan.dep_manager_reject_loan')[2]
            mtp = self.env['mail.template']
            template_id = mtp.browse(template_id)
            template_id.write({'email_to': self.employee_id.work_email})
            template_id.send_mail(self.ids[0], True)

    def action_close_loan(self):
        self.state = 'close'
        if self.employee_id.work_email and self.hr_manager_id:
            ir_model_data = self.env['ir.model.data']
            template_id = ir_model_data._xmlid_lookup('dev_hr_loan.hr_manager_closed_loan')
            mtp = self.env['mail.template']
            template_id = mtp.browse(template_id[1])
            template_id.write({'email_to': self.employee_id.work_email})
            template_id.send_mail(self.ids[0], True)



    def hr_manager_reject_loan(self):
        self.state = 'reject'
        employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        self.hr_manager_id = employee_id and employee_id.id or False
        if self.employee_id.work_email and self.hr_manager_id:
            ir_model_data = self.env['ir.model.data']
            template_id = ir_model_data._xmlid_lookup('dev_hr_loan.hr_manager_reject_loan')
            mtp = self.env['mail.template']
            template_id = mtp.browse(template_id[1])
            template_id.write({'email_to': self.employee_id.work_email})
            template_id.send_mail(self.ids[0], True)

    def cancel_loan(self):
        self.state = 'cancel'

    def set_to_draft(self):
        self.state = 'draft'
        self.hr_manager_id = False



    def paid_loan(self):
        if not self.employee_id.address_home_id:
            raise ValidationError(_('Employee Private Address is not selected in Employee Form !!!'))
            
        self.state = 'paid'
        vals={
            'date':self.date,
            'ref':self.name,
            'journal_id':self.loan_type_id.journal_id and self.loan_type_id.journal_id.id,
            'company_id':self.env.company.id
        }
        acc_move_id = self.env['account.move'].create(vals)
        if acc_move_id:
            lst = []
            val = (0,0,{
                            'account_id':self.loan_type_id and self.loan_type_id.loan_account.id,
                            'partner_id':self.employee_id.address_home_id and self.employee_id.address_home_id.id or False,
                            'name':self.name,
                            'credit':self.loan_amount or 0.0,
                            'move_id': acc_move_id.id,
                        })
            lst.append(val)

            if self.interest_amount:
                val = (0,0,{
                                'account_id':self.loan_type_id and self.loan_type_id.interest_account.id,
                                'partner_id':self.employee_id.address_home_id and self.employee_id.address_home_id.id or False,
                                'name':str(self.name)+' - '+'Interest',
                                'credit':self.interest_amount or 0.0,
                                'move_id': acc_move_id.id,
                            })
                lst.append(val)

            credit_account=False
            if self.employee_id.address_home_id and self.employee_id.address_home_id.property_account_payable_id:
                credit_account = self.employee_id.address_home_id.property_account_payable_id.id or False

            debit_amount = self.loan_amount
            if self.interest_amount:
                debit_amount += self.interest_amount
            val = (0,0,{
                            'account_id':credit_account or False,
                            'partner_id':self.employee_id.address_home_id and self.employee_id.address_home_id.id or False,
                            'name':'/',
                            'debit':debit_amount  or 0.0,
                            'move_id': acc_move_id.id,
                        })
            lst.append(val)
            acc_move_id.line_ids = lst
            self.move_id = acc_move_id.id
                    
                     

    def view_journal_entry(self):
        if self.move_id:
            return {
                'view_mode': 'form',
                'res_id': self.move_id.id,
                'res_model': 'account.move',
                'view_type': 'form',
                'type': 'ir.actions.act_window',
            }
            
            
    def action_done_loan(self):
        self.state = 'done'



    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'employee.loan') or '/'
        return super(employee_loan, self).create(vals)
        
    def copy(self, default=None):
        if default is None:
            default = {}
        default['name'] = '/'
        return super(employee_loan, self).copy(default=default)
    
    def unlink(self):
        for loan in self:
            if loan.state != 'draft':
                raise ValidationError(_('Loan delete in draft state only !!!'))
        return super(employee_loan,self).unlink()

    def action_view_loan_installment(self):
        action = self.env.ref('dev_hr_loan.action_installment_line').read()[0]

        installment = self.mapped('installment_lines')
        if len(installment) > 1:
            action['domain'] = [('id', 'in', installment.ids)]
        elif installment:
            action['views'] = [(self.env.ref('dev_hr_loan.view_loan_emi_form').id, 'form')]
            action['res_id'] = installment.id
        return action

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
