# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle 
#
##############################################################################

from odoo import api, fields, models, _


class import_logs(models.TransientModel):
    _name = "import.logs"


    name = fields.Text(string='Logs')
    
    
            

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:    
    
