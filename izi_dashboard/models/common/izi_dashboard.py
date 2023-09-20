# -*- coding: utf-8 -*-
# Copyright 2022 IZI PT Solusi Usaha Mudah
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
from random import randint


class IZIDashboard(models.Model):
    _name = 'izi.dashboard'
    _description = 'IZI Dashboard'
    _order = 'sequence,id'

    def _default_theme(self):
        default_theme = False
        try:
            default_theme = self.env.ref('izi_dashboard.izi_dashboard_theme_colorful').id
        except Exception as e:
            pass
        return default_theme

    name = fields.Char('Name', required=True)
    block_ids = fields.One2many(comodel_name='izi.dashboard.block',
                                inverse_name='dashboard_id', string='Dashboard Blocks')
    theme_id = fields.Many2one(comodel_name='izi.dashboard.theme', string='Theme', default=_default_theme)
    theme_name = fields.Char(related='theme_id.name')
    animation = fields.Boolean('Enable Animation', default=True)
    group_ids = fields.Many2many(comodel_name='res.groups', string='Groups')
    new_block_position = fields.Selection([
        ('top', 'Top'),
        ('bottom', 'Bottom'),
    ], default='top', string='New Chart Position', required=True)
    sequence = fields.Integer(string='Sequence')
    date_format = fields.Selection([
        ('today', 'Today'),
        ('this_week', 'This Week'),
        ('this_month', 'This Month'),
        ('this_year', 'This Year'),
        ('mtd', 'Month to Date'),
        ('ytd', 'Year to Date'),
        ('last_week', 'Last Week'),
        ('last_month', 'Last Month'),
        ('last_two_months', 'Last 2 Months'),
        ('last_three_months', 'Last 3 Months'),
        ('last_year', 'Last Year'),
        ('last_10', 'Last 10 Days'),
        ('last_30', 'Last 30 Days'),
        ('last_60', 'Last 60 Days'),
        ('custom', 'Custom Range'),
    ], default=False, string='Date Filter')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    menu_ids = fields.One2many('ir.ui.menu', 'dashboard_id', string='Menus')
    refresh_interval = fields.Integer('Refresh Interval in Seconds')

    @api.model
    def get_user_groups(self):
        manager_dashboard = self.env.ref('izi_dashboard.group_manager_dashboard')
        manager_analysis = self.env.ref('izi_data.group_manager_analysis')
        user_groups = self.env.user.groups_id
        user_dashboard = {
            'user_group_dashboard': 'Manager' if manager_dashboard.id in user_groups.ids else 'User',
            'user_group_analysis': 'Manager' if manager_analysis.id in user_groups.ids else 'User'
        }
        return user_dashboard

    def write(self, vals):
        if vals.get('refresh_interval', False) and vals.get('refresh_interval') < 10:
            raise ValidationError('Refresh interval have to be more than 10 seconds')
        res = super(IZIDashboard, self).write(vals)
        return res
    
    def action_save_and_close(self):
        return True

    def action_duplicate(self):
        self.ensure_one()
        self.copy({
            'name': '%s #%s' % (self.name, str(randint(1, 100000))),
        })


class IrMenu(models.Model):
    _inherit = 'ir.ui.menu'

    dashboard_id = fields.Many2one('izi.dashboard', string='Dashboard')
    
    @api.model
    def create(self, vals):
        rec = super(IrMenu, self).create(vals)
        if rec.dashboard_id:
            action = self.env['ir.actions.act_window'].create({
                'res_model': 'izi.dashboard',
                'target': 'current',
                'view_mode': 'izidashboard',
                'context': '''{'dashboard_id': %s}''' % (rec.dashboard_id.id)
            })
            rec.action = 'ir.actions.act_window,%s' % action.id
        return rec