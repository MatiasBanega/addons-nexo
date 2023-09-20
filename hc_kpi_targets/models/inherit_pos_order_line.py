# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class Customer(models.Model):
    _inherit = 'res.partner'

    partner_target = fields.Float('Customer Target')
    cust_type_ids = fields.Many2many('customer.type.target', string='Customer Type')

    @api.onchange('cust_type')
    def _onchange_cust_type(self):
        self.x_customer = False
        self.x_supplier = False
        self.x_service = False
        self.x_service = False
        if self.cust_type_ids:
            for rec in self.cust_type_ids:
                if rec.type == 'customer':
                    self.x_customer = True

                if rec.type == 'supplier':
                    self.x_supplier = True
                if rec.type == 'service':
                    self.x_service = True
                if rec.type == 'free':
                    self.x_service = True






class Team(models.Model):
    _inherit = 'crm.team'

    team_target = fields.Float('Sales Team Target')


class Salesperson(models.Model):
    _inherit = 'res.users'

    salesperson_target = fields.Float('Salesperson Target')


class ProductCateg(models.Model):
    _inherit = 'product.category'

    service_target = fields.Float('Service Categ Target')


class CustomerTypeTarget(models.Model):
    _name = 'customer.type.target'
    _description = 'Cust Type Target'

    customer_type_target = fields.Float('Customer Type Target')
    name = fields.Char('Name')
    type = fields.Selection([ ('customer', 'Customer'),
                              ('supplier', 'Supplier'),
                              ('service', 'Professional Service'),
                              ('free', 'Freelancer'),
                              ], string='Type', default=False)
