# -*- coding: utf-8 -*-
# Copyright 2022 IZI PT Solusi Usaha Mudah
import sqlparse

from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from random import randint


class IZIAnalysisCategory(models.Model):
    _name = 'izi.analysis.category'
    _description = 'IZI Analysis Category'

    name = fields.Char(string='Name', required=True)

class IZIAnalysis(models.Model):
    _name = 'izi.analysis'
    _description = 'IZI Analysis'

    name = fields.Char(string='Name', required=True)
    source_id = fields.Many2one('izi.data.source', string='Data Source', required=True, ondelete='cascade')
    source_type = fields.Selection(string='Data Source Type', related='source_id.type')
    method = fields.Selection([
        ('model', 'Odoo Model'),
        ('table_view', 'Table View'),
        ('query', 'Direct Query'),
        ('table', 'Mart Table'),
        ('kpi', 'Key Performance Indicator'),
    ], default='model', string='Method', required=True)
    table_name = fields.Char('Table View Name')
    table_id = fields.Many2one('izi.table', string='Table', required=False, ondelete='cascade')
    table_view_id = fields.Many2one('izi.table', string='Table', required=False, ondelete='cascade')
    table_model_id = fields.Many2one('izi.table', string='Table', required=False, ondelete='cascade')
    db_query = fields.Text('Database Query', related='table_id.db_query', readonly=False, store=True)
    metric_ids = fields.One2many('izi.analysis.metric', 'analysis_id', string='Metrics', required=True)
    dimension_ids = fields.One2many('izi.analysis.dimension', 'analysis_id', string='Dimensions')
    filter_temp_ids = fields.One2many('izi.analysis.filter.temp', 'analysis_id', string='Filters Temp')
    filter_ids = fields.One2many('izi.analysis.filter', 'analysis_id', string='Filters')
    limit = fields.Integer(string='Limit', default=100)
    query_preview = fields.Text(string='Query Preview', compute='get_query_preview')
    sort_ids = fields.One2many(comodel_name='izi.analysis.sort', inverse_name='analysis_id', string="Sorts")
    field_ids = fields.Many2many(comodel_name='izi.table.field', compute='_get_analysis_fields')
    group_ids = fields.Many2many(comodel_name='res.groups', string='Groups')
    date_field_id = fields.Many2one('izi.table.field', string='Date Field')
    model_id = fields.Many2one('ir.model', string='Model')
    model_name = fields.Char('Model Name', related='model_id.model')
    domain = fields.Char('Domain')
    category_id = fields.Many2one('izi.analysis.category', string='Category')
    kpi_id = fields.Many2one('izi.kpi', 'Key Performance Indicator')
    kpi_auto_calculate = fields.Boolean('Auto Calculate When Open Dashboard', default=False)
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

    _sql_constraints = [
        ('name_table_unique', 'unique(name, table_id)', 'Analysis Name Already Exist.')
    ]

    @api.onchange('method')
    def onchange_method(self):
        self.ensure_one()
        self.table_model_id = False
        self.table_view_id = False
        self.table_id = False
        if self.method != 'kpi':
            self.kpi_id = False

    @api.onchange('kpi_id')
    def onchange_kpi_id(self):
        self.ensure_one()
        if self.method == 'kpi' and self.kpi_id:
            table = self.env['izi.table'].search([('model_id.model', '=', 'izi.kpi.line')], limit=1)
            if not table:
                raise UserError('Table Key Performance Indicator is not found!')
            self.table_model_id = table.id
            self.name = self.kpi_id.name or 'New Analysis'
            self.domain = '''[('kpi_id', '=', %s)]''' % (self.kpi_id.id)

    @api.onchange('table_view_id')
    def onchange_table_view_id(self):
        self.ensure_one()
        if self.table_view_id:
            self.table_id = self.table_view_id.id

    @api.onchange('table_model_id')
    def onchange_table_model_id(self):
        self.ensure_one()
        if self.table_model_id:
            self.table_id = self.table_model_id.id

    @api.onchange('table_id')
    def onchange_table_id(self):
        self.ensure_one()
        self.filter_ids = False
        self.sort_ids = False
        self.metric_ids = False
        self.dimension_ids = False
        self.model_id = False
        self.domain = False
        self.date_field_id = False
        if self.table_model_id:
            self.model_id = self.table_model_id.model_id.id
        if self.method == 'table' and self.table_id and self.table_id.store_table_name and not self.db_query:
            self.db_query = '''SELECT * \nFROM %s \nLIMIT 100;''' % (self.table_id.store_table_name)
        if self.method == 'kpi' and self.kpi_id:
            self.domain = '''[('kpi_id', '=', %s)]''' % (self.kpi_id.id)
            for field in self.table_id.field_ids.sorted('name', reverse=True):
                if field.field_name == 'value' or field.field_name == 'target':
                    self.metric_ids = [(0, 0, {
                        'field_id': field.id,
                        'calculation': 'sum',
                    })]
                elif field.field_name == 'date':
                    self.dimension_ids = [(0, 0, {
                        'field_id': field.id,
                        'field_format': self.kpi_id.interval,
                    })]
                    self.date_field_id = field.id

    def action_save_and_close(self):
        return True

    def action_duplicate(self):
        self.ensure_one()
        self.copy({
            'name': '%s #%s' % (self.name, str(randint(1, 100000))),
        })

    def action_refresh_table_list(self):
        self.ensure_one()
        if self.source_id:
            self.source_id.get_source_tables()
        if self.env.context.get('from_ui', False):
            return {
                'type': 'ir.actions.act_window',
                'name': 'Analysis',
                'target': 'new',
                'res_id': self.id,
                'res_model': 'izi.analysis',
                'views': [[False, 'form']],
                'context': {'active_test': False},
            }

    def _set_default_metric(self):
        self.ensure_one()
        self.filter_ids.unlink()
        self.sort_ids.unlink()
        self.metric_ids.unlink()
        self.dimension_ids.unlink()
        
        Field = self.env['izi.table.field']
        # Default Metric
        metric_field = Field.search([('field_type', 'in', ('numeric', 'number')),
                                    ('table_id', '=', self.table_id.id)], limit=1, order='id asc')
        if not metric_field:
            metric_field = Field.search([('field_type', 'in', ('numeric', 'number')),
                                        ('table_id', '=', self.table_id.id)], limit=1)
        if metric_field:
            self.metric_ids = [(0, 0, {
                'field_id': metric_field.id,
                'calculation': 'count',
            })]
    
    def build_query(self):
        self.ensure_one()
        if self.method == 'query':
            table = self.env['izi.table'].search([('name', '=', self.name), ('is_query', '=', True)], limit=1)
            if not table:
                table = self.env['izi.table'].create({
                    'name': self.name,
                    'source_id': self.source_id.id,
                    'is_query': True,
                    'db_query': self.db_query,
                })
            table.get_table_fields()
            self._set_default_metric()
            self.table_id = table.id
            return {
                'type': 'ir.actions.act_window',
                'name': 'Analysis',
                'target': 'new',
                'res_id': self.id,
                'res_model': 'izi.analysis',
                'views': [[False, 'form']],
            }
    
    def get_table_datas(self):
        self.ensure_one()
        return self.table_id.with_context(test_query=True).get_table_datas()

    @api.model
    def create(self, vals):
        res = super(IZIAnalysis, self).create(vals)
        for analysis in res:
            if not analysis.metric_ids:
                analysis._set_default_metric()
        return res

    def write(self, vals):
        res = super(IZIAnalysis, self).write(vals)
        for analysis in self:
            if not analysis.metric_ids:
                analysis._set_default_metric()
        return res

    @api.depends('metric_ids', 'dimension_ids')
    def _get_analysis_fields(self):
        for analysis in self:
            field_ids = []
            for metric in analysis.metric_ids:
                field_ids.append(metric.field_id.id)
            for dimension in analysis.dimension_ids:
                field_ids.append(dimension.field_id.id)
            analysis.field_ids = list(set(field_ids))

    def get_query_preview(self):
        res_metrics = []
        res_dimensions = []
        res_fields = []

        # query variable
        dimension_query = ''
        dimension_queries = []
        metric_query = ''
        metric_queries = []
        sort_query = ''
        sort_queries = []
        filter_query = "'IZI' = 'IZI'"
        filter_queries = []
        limit_query = ''

        # Build Dimension Query
        func_get_field_metric_format = getattr(self, 'get_field_metric_format_%s' % self.source_id.type)
        func_get_field_dimension_format = getattr(self, 'get_field_dimension_format_%s' % self.source_id.type)
        func_get_field_sort = getattr(self, 'get_field_sort_format_%s' % self.source_id.type)
        if self.table_id.is_stored:
            func_get_field_metric_format = getattr(self, 'get_field_metric_format_db_odoo')
            func_get_field_dimension_format = getattr(self, 'get_field_dimension_format_db_odoo')
            func_get_field_sort = getattr(self, 'get_field_sort_format_db_odoo')
        for dimension in self.dimension_ids:
            dimension_alias = dimension.field_id.name
            if dimension.name_alias:
                dimension_alias = dimension.name_alias
            dimension_metric = func_get_field_metric_format(
                **{'field_name': dimension.field_id.field_name, 'field_type': dimension.field_id.field_type,
                   'field_format': dimension.field_format})
            dimension_field = func_get_field_dimension_format(
                **{'field_name': dimension.field_id.field_name, 'field_type': dimension.field_id.field_type,
                   'field_format': dimension.field_format})
            metric_queries.append('%s as "%s"' % (dimension_metric, dimension_alias))
            dimension_queries.append('%s' % (dimension_field))
            res_dimensions.append(dimension_alias)
            res_fields.append(dimension_alias)

        # Build Metric Query
        for metric in self.metric_ids:
            metric_alias = "%s of %s" % (metric.calculation.title(), metric.field_id.name)
            if metric.name_alias:
                metric_alias = metric.name_alias
            metric_queries.append('%s(%s) as "%s"' % (metric.calculation, metric.field_id.field_name, metric_alias))
            res_metrics.append(metric_alias)
            res_fields.append(metric_alias)

        # Build Filter Query
        for fltr in self.filter_ids:
            open_bracket = ''
            close_bracket = ''
            if fltr.open_bracket:
                open_bracket = '('
            if fltr.close_bracket:
                close_bracket = ')'

            fltr_value = ' %s' % fltr.value.replace("'", '').replace('"', '')
            if fltr.field_type == 'string':
                fltr_value = ' \'%s\'' % fltr.value.replace("'", '').replace('"', '')

            fltr_str = '%s %s%s %s %s%s' % (fltr.condition, open_bracket,
                                            fltr.field_id.field_name, fltr.operator_id.name, fltr_value, close_bracket)
            filter_queries.append(fltr_str)

        filter_query += ' %s' % ' '.join(filter_queries)

        # Build Sort Query
        for sort in self.sort_ids:
            if sort.field_format:
                field_sort = func_get_field_sort(
                    **{'field_name': sort.field_id.field_name, 'field_type': sort.field_id.field_type,
                       'field_format': sort.field_format, 'sort': sort.sort})
                sort_queries.append(field_sort)
            elif sort.field_calculation:
                sort_queries.append('%s(%s) %s' % (sort.field_calculation, sort.field_id.field_name, sort.sort))
            else:
                sort_queries.append('%s %s' % (sort.field_id.field_name, sort.sort))

        # Build Query
        # SELECT operation(metric) FROM table WHERE filter GROUP BY dimension ORDER BY sort
        metric_query = ', '.join(metric_queries)
        dimension_query = ', '.join(dimension_queries)
        table_query = self.table_id.table_name
        sort_query = ', '.join(sort_queries)

        # Check
        if not self.table_id.table_name:
            if self.table_id.is_stored:
                table_query = self.table_id.store_table_name
            else:
                table_query = self.table_id.db_query or ''
                table_query = table_query.replace(';', '')
                table_query = '(%s) table_query' % (table_query)
        if filter_query:
            filter_query = 'WHERE %s' % (filter_query)
        if dimension_query:
            dimension_query = 'GROUP BY %s' % (dimension_query)
        if sort_query:
            sort_query = 'ORDER BY %s' % (sort_query)
        if self.limit:
            if self.limit > 0:
                limit_query = 'LIMIT %s' % (self.limit)

        query = '''
            SELECT
                %s
            FROM
                %s
            %s
            %s
            %s
            %s;
        ''' % (metric_query, table_query, filter_query, dimension_query, sort_query, limit_query)

        self.query_preview = sqlparse.format(query, reindent=True, keyword_case='upper')

    def get_analysis_data(self, **kwargs):
        self.ensure_one()
        if self.method in ('model', 'kpi'):
            if self.method == 'kpi' and self.kpi_id and self.kpi_auto_calculate:
                self.kpi_id.action_calculate_value()
            return self.get_analysis_data_model(**kwargs)
        else:
            return self.get_analysis_data_query(**kwargs)

    def get_analysis_data_model(self, **kwargs):
        self.ensure_one()
        if not self.metric_ids:
            return {
                'data': [],
                'metrics': [],
                'dimensions': [],
                'fields': [],
                'values': [],
            }
            raise ValidationError('To query the data, analysis must have at least one metric')
        if not self.model_id:
            raise ValidationError('To query the data with odoo orm, analysis must use table from odoo model')

        res_data = []
        res_metrics = []
        res_dimensions = []
        res_fields = []
        res_values = []

        dimension_queries = []
        metric_queries = []
        sort_queries = []
        alias_by_field_name = {}
        field_names = []
        metric_field_names = []
        selection_dict_by_field_name = {}

        max_dimension = False
        if 'max_dimension' in kwargs:
            max_dimension = kwargs.get('max_dimension')

        # Dimension
        count_dimension = 0
        for dimension in self.dimension_ids:
            # Date Format
            if dimension.field_id.field_type in ('date', 'datetime') and dimension.field_format:
                field_name = '%s:%s' % (dimension.field_id.field_name, dimension.field_format)
            else:
                field_name = dimension.field_id.field_name
            # Check If Selection
            if self.env[self.model_id.model]._fields.get(dimension.field_id.field_name, False):
                if self.env[self.model_id.model]._fields.get(dimension.field_id.field_name).type == 'selection':
                    selection_dict_by_field_name[field_name] = dict(self.env[self.model_id.model]._fields[dimension.field_id.field_name].selection)
            dimension_queries.append(field_name)
            field_names.append(field_name)
            # Field Alias
            dimension_alias = dimension.field_id.name
            if dimension.name_alias:
                dimension_alias = dimension.name_alias
            res_dimensions.append(dimension_alias)
            res_fields.append(dimension_alias)
            alias_by_field_name[field_name] = dimension_alias
            count_dimension += 1
            if max_dimension:
                if count_dimension >= max_dimension:
                    break
       
        # Metric
        for metric in self.metric_ids:
            metric_alias = "%s of %s" % (metric.calculation.title(), metric.field_id.name)
            field_name = metric_alias.lower().replace(' ', '_')
            field_names.append(field_name)
            metric_field_names.append(field_name)
            # Field Alias
            if metric.name_alias:
                metric_alias = metric.name_alias
            metric_queries.append('%s:%s(%s)' % (field_name, metric.calculation.lower(), metric.field_id.field_name))
            res_metrics.append(metric_alias)
            res_fields.append(metric_alias)
            alias_by_field_name[field_name] = metric_alias

        # Sort
        for sort in self.sort_ids:
            sort_query = '%s %s' % (sort.field_id.field_name, sort.sort)
            for metric in self.metric_ids:
                if sort.field_id == metric.field_id:
                    metric_alias = "%s of %s" % (metric.calculation.title(), metric.field_id.name)
                    field_name = metric_alias.lower().replace(' ', '_')
                    sort_query = '%s %s' % (field_name, sort.sort)
                    break
            sort_queries.append(sort_query)
        sort_queries = (',').join(sort_queries)

        # Data
        domain = []
        if self.domain:
            domain = safe_eval(self.domain)
        if kwargs.get('filters'):
            # Check Default Date Filter In Analysis If Filters Empty
            if self.date_field_id and not kwargs.get('filters').get('date_format'):
                if self.date_format:
                    kwargs['filters']['date_format'] = self.date_format
                    if self.date_format == 'custom' and (self.start_date or self.end_date):
                        kwargs['filters']['date_range'] = [self.start_date, self.end_date]
            # Process Date Filter
            if self.date_field_id and kwargs.get('filters').get('date_format'):
                start_date = False
                end_date = False
                start_datetime = False
                end_datetime = False
                date_format = kwargs.get('filters').get('date_format')
                if date_format == 'custom' and kwargs.get('filters').get('date_range'):
                    date_range = kwargs.get('filters').get('date_range')
                    start_date = date_range[0]
                    end_date = date_range[1]
                    if start_date:
                        start_datetime = start_date + ' 00:00:00'
                    if end_date:
                        end_datetime = end_date + ' 23:59:59'
                elif date_format != 'custom':
                    date_range = self.get_date_range_by_date_format(date_format)
                    start_date = date_range.get('start_date')
                    end_date = date_range.get('end_date')
                    start_datetime = date_range.get('start_datetime')
                    end_datetime = date_range.get('end_datetime')
                # Create Domain
                if self.date_field_id.field_type == 'date':
                    if start_date:
                        domain.append((self.date_field_id.field_name, '>=', start_date))
                    if end_date:
                        domain.append((self.date_field_id.field_name, '<=', end_date))
                if self.date_field_id.field_type == 'datetime':
                    if start_datetime:
                        domain.append((self.date_field_id.field_name, '>=', start_datetime))
                    if end_datetime:
                        domain.append((self.date_field_id.field_name, '<=', end_datetime))
        records = self.env[self.model_id.model].read_group(domain, metric_queries, dimension_queries, limit=self.limit, orderby=sort_queries, lazy=False)
        res_data = []
        for record in records:
            dict_value = {}
            for field_name in field_names:
                value = False
                key = field_name
                if record.get(field_name):
                    value = record.get(field_name)
                    if type(record.get(field_name)) is tuple:
                        value = record.get(field_name)[1]
                        if value._value:
                            value = value._value
                # Set Key to Field Alias
                if alias_by_field_name.get(field_name):
                    key = alias_by_field_name.get(field_name)
                # Set Value If Null
                if not value:
                    if field_name in metric_field_names:
                        value = 0
                    else:
                        value = ''
                # Set Selection Label
                if field_name in selection_dict_by_field_name:
                    selection_dict = selection_dict_by_field_name[field_name]
                    if value in selection_dict:
                        value = selection_dict[value]
                dict_value[key] = value
            res_data.append(dict_value)

        # Values
        for record in res_data:
            res_value = []
            for key in record:
                res_value.append(record[key])
            res_values.append(res_value)
        
        result = {
            'data': res_data,
            'metrics': res_metrics,
            'dimensions': res_dimensions,
            'fields': res_fields,
            'values': res_values,
        }

        if 'test_analysis' not in self._context:
            return result
        else:
            title = _("Successfully Get Data Analysis")
            message = _("""
                Your analysis looks fine!
                Sample Data:
                %s
            """ % (str(result.get('data')[0]) if result.get('data') else str(result.get('data'))))
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': title,
                    'message': message,
                    'sticky': False,
                }
            }

    def get_analysis_data_query(self, **kwargs):
        self.ensure_one()
        if not self.metric_ids:
            return {
                'data': [],
                'metrics': [],
                'dimensions': [],
                'fields': [],
                'values': [],
            }
            raise ValidationError('To query the data, analysis must have at least one metric')

        res_data = []
        res_metrics = []
        res_dimensions = []
        res_fields = []
        res_values = []

        # query variable
        dimension_query = ''
        dimension_queries = []
        metric_query = ''
        metric_queries = []
        sort_query = ''
        sort_queries = []
        filter_query = "'IZI' = 'IZI'"
        filter_queries = []
        filter_temp_result_list = []
        limit_query = ''
        dashboard_filter_queries = []

        max_dimension = False
        if 'max_dimension' in kwargs:
            max_dimension = kwargs.get('max_dimension')

        # Build Dimension Query
        func_get_field_metric_format = getattr(self, 'get_field_metric_format_%s' % self.source_id.type)
        func_get_field_dimension_format = getattr(self, 'get_field_dimension_format_%s' % self.source_id.type)
        func_get_field_sort = getattr(self, 'get_field_sort_format_%s' % self.source_id.type)
        if self.table_id.is_stored:
            func_get_field_metric_format = getattr(self, 'get_field_metric_format_db_odoo')
            func_get_field_dimension_format = getattr(self, 'get_field_dimension_format_db_odoo')
            func_get_field_sort = getattr(self, 'get_field_sort_format_db_odoo')
        count_dimension = 0
        for dimension in self.dimension_ids:
            dimension_alias = dimension.field_id.name
            if dimension.name_alias:
                dimension_alias = dimension.name_alias
            dimension_metric = func_get_field_metric_format(
                **{'field_name': dimension.field_id.field_name, 'field_type': dimension.field_id.field_type,
                   'field_format': dimension.field_format})
            dimension_field = func_get_field_dimension_format(
                **{'field_name': dimension.field_id.field_name, 'field_type': dimension.field_id.field_type,
                   'field_format': dimension.field_format})
            metric_queries.append('%s as "%s"' % (dimension_metric, dimension_alias))
            dimension_queries.append('%s' % (dimension_field))
            res_dimensions.append(dimension_alias)
            res_fields.append(dimension_alias)

            count_dimension += 1
            if max_dimension:
                if count_dimension >= max_dimension:
                    break

        # Build Metric Query
        for metric in self.metric_ids:
            metric_alias = "%s of %s" % (metric.calculation.title(), metric.field_id.name)
            if metric.name_alias:
                metric_alias = metric.name_alias
            metric_queries.append('%s(%s) as "%s"' % (metric.calculation, metric.field_id.field_name, metric_alias))
            res_metrics.append(metric_alias)
            res_fields.append(metric_alias)

        # Build Filter Query
        for fltr in self.filter_ids:
            open_bracket = ''
            close_bracket = ''
            if fltr.open_bracket:
                open_bracket = '('
            if fltr.close_bracket:
                close_bracket = ')'

            fltr_value = ' %s' % fltr.value.replace("'", '').replace('"', '')
            if fltr.field_type == 'string':
                fltr_value = ' \'%s\'' % fltr.value.replace("'", '').replace('"', '')

            fltr_str = '%s %s%s %s %s%s' % (fltr.condition, open_bracket,
                                            fltr.field_id.field_name, fltr.operator_id.name, fltr_value, close_bracket)
            filter_queries.append(fltr_str)

        filter_query += ' %s' % ' '.join(filter_queries)

        # Build Dashboard Date Filter Query
        if kwargs.get('filters'):
            if self.date_field_id and kwargs.get('filters').get('date_format'):
                start_date = False
                end_date = False
                start_datetime = False
                end_datetime = False
                date_format = kwargs.get('filters').get('date_format')
                if date_format == 'custom' and kwargs.get('filters').get('date_range'):
                    date_range = kwargs.get('filters').get('date_range')
                    start_date = date_range[0]
                    end_date = date_range[1]
                    if start_date:
                        start_datetime = start_date + ' 00:00:00'
                    if end_date:
                        end_datetime = end_date + ' 23:59:59'
                elif date_format != 'custom':
                    date_range = self.get_date_range_by_date_format(date_format)
                    start_date = date_range.get('start_date')
                    end_date = date_range.get('end_date')
                    start_datetime = date_range.get('start_datetime')
                    end_datetime = date_range.get('end_datetime')
                # Create Query
                if self.date_field_id.field_type == 'date':
                    if start_date:
                        dashboard_filter_queries.append('(%s >= $$%s$$)' % (self.date_field_id.field_name, start_date))
                    if end_date:
                        dashboard_filter_queries.append('(%s <= $$%s$$)' % (self.date_field_id.field_name, end_date))
                if self.date_field_id.field_type == 'datetime':
                    if start_datetime:
                        dashboard_filter_queries.append('(%s >= $$%s$$)' % (self.date_field_id.field_name, start_datetime))
                    if end_datetime:
                        dashboard_filter_queries.append('(%s <= $$%s$$)' % (self.date_field_id.field_name, end_datetime))
        if dashboard_filter_queries:
            dashboard_filter_query = (' and ').join(dashboard_filter_queries)
            filter_query += ' and (%s)' % dashboard_filter_query
            
        # Build Filter Temp Query
        func_get_filter_temp_query = getattr(self, 'get_filter_temp_query_%s' % self.source_id.type)
        if 'filter_temp_values' in kwargs:
            for filter_value in kwargs.get('filter_temp_values'):
                result_query = func_get_filter_temp_query(**{'filter_value': filter_value})
                filter_temp_result_list.append(result_query)

        for filter_temp_result in filter_temp_result_list:
            if filter_temp_result is False:
                continue

            filter_sub_query = False
            filter_sub_query = ' {join_operator} '.format(
                join_operator=filter_temp_result.get('join_operator')).join(filter_temp_result.get('query'))

            if filter_sub_query:
                filter_query += ' and (%s)' % filter_sub_query

        # Build Sort Query
        for sort in self.sort_ids:
            if sort.field_format:
                field_sort = func_get_field_sort(
                    **{'field_name': sort.field_id.field_name, 'field_type': sort.field_id.field_type,
                       'field_format': sort.field_format, 'sort': sort.sort})
                sort_queries.append(field_sort)
            elif sort.field_calculation:
                sort_queries.append('%s(%s) %s' % (sort.field_calculation, sort.field_id.field_name, sort.sort))
            else:
                sort_queries.append('%s %s' % (sort.field_id.field_name, sort.sort))

        # Build Query
        # SELECT operation(metric) FROM table WHERE filter GROUP BY dimension ORDER BY sort
        metric_query = ', '.join(metric_queries)
        dimension_query = ', '.join(dimension_queries)
        table_query = self.table_id.table_name
        sort_query = ', '.join(sort_queries)

        # Check
        if not self.table_id.table_name:
            if self.table_id.is_stored:
                table_query = self.table_id.store_table_name
            else:
                table_query = self.table_id.db_query.replace(';', '')
                table_query = '(%s) table_query' % (table_query)
        if filter_query:
            filter_query = 'WHERE %s' % (filter_query)
        if dimension_query:
            dimension_query = 'GROUP BY %s' % (dimension_query)
        if sort_query:
            sort_query = 'ORDER BY %s' % (sort_query)
        if self.limit:
            if self.limit > 0:
                limit_query = 'LIMIT %s' % (self.limit)

        query = '''
            SELECT
                %s
            FROM
                %s
            %s
            %s
            %s
            %s;
        ''' % (metric_query, table_query, filter_query, dimension_query, sort_query, limit_query)

        func_check_query = getattr(self.source_id, 'check_query_%s' % self.source_id.type)
        func_check_query(**{
            'query': table_query,
        })

        result = {'res_data': []}
        if self.table_id.is_stored:
            self.env.cr.execute(query)
            result['res_data'] = self.env.cr.dictfetchall()
        else:
            func_get_analysis_data = getattr(self, 'get_analysis_data_%s' % self.source_id.type)
            result = func_get_analysis_data(**{
                'query': query,
            })

        res_data = result.get('res_data')

        for record in res_data:
            res_value = []
            for key in record:
                res_value.append(record[key])
            res_values.append(res_value)

        result = {
            'data': res_data,
            'metrics': res_metrics,
            'dimensions': res_dimensions,
            'fields': res_fields,
            'values': res_values,
        }

        if 'test_analysis' not in self._context:
            return result
        else:
            title = _("Successfully Get Data Analysis")
            message = _("""
                Your analysis looks fine!
                Sample Data:
                %s
            """ % (str(result.get('data')[0]) if result.get('data') else str(result.get('data'))))
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': title,
                    'message': message,
                    'sticky': False,
                }
            }

    def field_format_query(self, field_name, field_type, field_format):
        query = '%s' % (field_name)
        if not field_format:
            return query
        if field_type in ('date', 'datetime'):
            date_format = {
                'year': 'YYYY',
                'month': 'MON YYYY',
                'week': 'DD MON YYYY',
                'day': 'DD MON YYYY',
            }
            if field_format in date_format:
                query = '''to_char(date_trunc('%s', %s), '%s')''' % (
                    field_format, field_name, date_format[field_format])
        return query

    def get_date_range_by_date_format(self, date_format):
        # Today
        start_date = datetime.today()
        end_date = datetime.today()

        if date_format == 'this_week':
            start_date = start_date - timedelta(days=start_date.weekday())
            end_date = start_date + timedelta(days=6)
        elif date_format == 'last_week':
            start_date = start_date - timedelta(days=7)
            start_date = start_date - timedelta(days=start_date.weekday())
            end_date = start_date + timedelta(days=6)
        elif date_format == 'last_10':
            start_date = start_date - timedelta(days=10)
        elif date_format == 'last_30':
            start_date = start_date - timedelta(days=30)
        elif date_format == 'last_60':
            start_date = start_date - timedelta(days=60)
        elif date_format == 'before_today':
            start_date = start_date.replace(year=start_date.year - 50)
            end_date = end_date - timedelta(days=1)
        elif date_format == 'after_today':
            start_date = start_date + timedelta(days=1)
            end_date = end_date.replace(year=end_date.year + 50)
        elif date_format == 'before_and_today':
            start_date = start_date.replace(year=start_date.year - 50)
        elif date_format == 'today_and_after':
            end_date = end_date.replace(year=end_date.year + 50)
        elif date_format == 'this_month':
            start_date = start_date.replace(day=1)
            next_month = start_date.replace(day=28) + timedelta(days=4)
            end_date = next_month - timedelta(days=next_month.day)
        elif date_format == 'mtd':
            start_date = start_date.replace(day=1)
            end_date = datetime.today()
        elif date_format == 'last_month':
            start_date = start_date.replace(day=1) - timedelta(days=1)
            start_date = start_date.replace(day=1)
            next_month = start_date.replace(day=28) + timedelta(days=4)
            end_date = next_month - timedelta(days=next_month.day)
        elif date_format == 'last_two_months':
            next_month = start_date.replace(day=28) + timedelta(days=4)
            start_date = start_date.replace(day=1) - timedelta(days=1)
            start_date = start_date.replace(day=1)
            end_date = next_month - timedelta(days=next_month.day)
        elif date_format == 'last_three_months':
            next_month = start_date.replace(day=28) + timedelta(days=4)
            start_date = start_date.replace(day=1) - timedelta(days=1)
            start_date = start_date.replace(day=1) - timedelta(days=1)
            start_date = start_date.replace(day=1)
            end_date = next_month - timedelta(days=next_month.day)
        elif date_format == 'this_year':
            start_date = start_date.replace(day=1, month=1)
            end_date = end_date.replace(day=31, month=12)
        elif date_format == 'ytd':
            start_date = start_date.replace(day=1, month=1)
            end_date = datetime.today()
        elif date_format == 'last_year':
            start_date = start_date - relativedelta(years=1)
            start_date = start_date.replace(day=1, month=1)
            end_date = start_date.replace(day=31, month=12)

        start_date = start_date.strftime("%Y-%m-%d")
        end_date = end_date.strftime("%Y-%m-%d")
        start_datetime = start_date + ' 00:00:00'
        end_datetime = end_date + ' 23:59:59'

        return {
            'start_date': start_date,
            'end_date': end_date,
            'start_datetime': start_datetime,
            'end_datetime': end_datetime,
        }


class IZIAnalysisMetric(models.Model):
    _name = 'izi.analysis.metric'
    _description = 'IZI Analysis Metric'
    _order = 'id'

    sequence = fields.Integer('Sequence')
    analysis_id = fields.Many2one('izi.analysis', string='Analysis', required=True, ondelete='cascade')
    table_id = fields.Many2one('izi.table', string='Table', related='analysis_id.table_id')
    field_id = fields.Many2one('izi.table.field', string='Field', required=True)
    field_type = fields.Char('Field Type', related='field_id.field_type')
    name = fields.Char('Name', related='field_id.name', store=True)
    name_alias = fields.Char(string="Alias")
    calculation = fields.Selection([
        ('count', 'Count'),
        ('sum', 'Sum'),
        ('avg', 'Avg'),
    ], string='Calculation', required=True, default='sum')
    sort = fields.Selection([
        ('asc', 'Ascending'),
        ('desc', 'Descending'),
    ], string='Sort', required=False, default=False)

    @api.onchange('field_id')
    def onchange_field_id(self):
        for metric in self:
            for sort in metric.analysis_id.sort_ids:
                if sort.field_id == metric._origin.field_id:
                    raise ValidationError(
                        'This metric field is used to sorting the analysis! Please remove the sort that using this'
                        + ' field and try to change this metric field again!')

    @api.onchange('calculation')
    def onchange_calculation(self):
        for metric in self:
            for sort in metric.analysis_id.sort_ids:
                if sort.field_id == metric._origin.field_id:
                    raise ValidationError(
                        'This metric field is used to sorting the analysis! Please remove the sort that using this'
                        + ' field and try to change this metric field again!')


class IZIAnalysisDimension(models.Model):
    _name = 'izi.analysis.dimension'
    _description = 'IZI Analysis Demension'
    _order = 'id'

    sequence = fields.Integer('Sequence')
    analysis_id = fields.Many2one('izi.analysis', string='Analysis', required=True, ondelete='cascade')
    table_id = fields.Many2one('izi.table', string='Table', related='analysis_id.table_id')
    field_id = fields.Many2one('izi.table.field', string='Field', required=True)
    field_type = fields.Char('Field Type', related='field_id.field_type')
    field_format = fields.Selection(selection=[
        ('day', 'Day'),
        ('week', 'Week'),
        ('month', 'Month'),
        ('year', 'Year'),
    ], string='Field Format')
    name = fields.Char('Name', related='field_id.name', store=True)
    name_alias = fields.Char(string="Alias")
    sort = fields.Selection([
        ('asc', 'Ascending'),
        ('desc', 'Descending'),
    ], string='Sort', required=False, default=False)

    @api.onchange('field_id')
    def onchange_field_id(self):
        for dimension in self:
            if dimension.field_type not in ['date', 'datetime']:
                dimension.field_format = False
            for sort in dimension.analysis_id.sort_ids:
                if sort.field_id == dimension._origin.field_id:
                    raise ValidationError(
                        'This dimension field is used to sorting the analysis! Please remove the sort that using this'
                        + ' field and try to change this dimension field again!')

    @api.onchange('field_format')
    def onchange_field_format(self):
        for dimension in self:
            for sort in dimension.analysis_id.sort_ids:
                if sort.field_id == dimension._origin.field_id:
                    raise ValidationError(
                        'This dimension field is used to sorting the analysis! Please remove the sort that using this'
                        + ' field and try to change this dimension field again!')


class IZIAnalysisFilterTemp(models.Model):
    _name = 'izi.analysis.filter.temp'
    _description = 'IZI Analysis Filter Temp'

    analysis_id = fields.Many2one('izi.analysis', string='Analysis', required=True, ondelete='cascade')
    table_id = fields.Many2one('izi.table', string='Table', related='analysis_id.table_id')
    field_id = fields.Many2one('izi.table.field', string='Field', required=True, ondelete='cascade')
    field_type = fields.Char('Field Type', related='field_id.field_type')
    type = fields.Selection(selection=[
        ('string_search', 'String Search'),
        ('date_range', 'Date Range'),
        ('date_format', 'Date Format'),
    ], string='Filter Type')
    name = fields.Char('Name', related='field_id.name', store=True)


class IZIAnalysisFilter(models.Model):
    _name = 'izi.analysis.filter'
    _description = 'IZI Analysis Filter'
    _order = 'id'

    analysis_id = fields.Many2one('izi.analysis', string='Analysis', required=True, ondelete='cascade')
    table_id = fields.Many2one('izi.table', string='Table', related='analysis_id.table_id')
    source_id = fields.Many2one('izi.data.source', string='Data Source', related='analysis_id.source_id')
    source_type = fields.Selection(string='Data Source Type', related='analysis_id.source_id.type')
    field_id = fields.Many2one('izi.table.field', string='Field', required=True, ondelete='cascade')
    operator_id = fields.Many2one(comodel_name='izi.analysis.filter.operator', string='Operator', required=True)
    field_type = fields.Char(string='Field Type', related='field_id.field_type')
    value = fields.Char(string='Value')
    open_bracket = fields.Boolean(string='Open Bracket')
    close_bracket = fields.Boolean(string='Close Bracket')
    condition = fields.Selection(string='Condition', selection=[
        ('and', 'AND'),
        ('or', 'OR'),
    ], required=True)


class IZIAnalysisFilterOperator(models.Model):
    _name = 'izi.analysis.filter.operator'
    _description = 'IZI Analysis Filter Operator'
    _order = 'id'

    name = fields.Char(string='Name')
    source_type = fields.Selection([], string='Source Type')


class IZIAnalysisSort(models.Model):
    _name = 'izi.analysis.sort'
    _description = 'IZI Analysis Sort'
    _order = 'id'

    sequence = fields.Integer(string='Sequence')
    analysis_id = fields.Many2one(comodel_name='izi.analysis', string='Analysis', required=True, ondelete='cascade')
    table_id = fields.Many2one(comodel_name='izi.table', string='Table', related='analysis_id.table_id')
    source_id = fields.Many2one(comodel_name='izi.data.source', string='Data Source', related='analysis_id.source_id')
    source_type = fields.Selection(string='Data Source Type', related='analysis_id.source_id.type')
    field_id = fields.Many2one(comodel_name='izi.table.field', string='Field', required=True)
    field_type = fields.Char(string='Field Type', related='field_id.field_type')
    metric_id = fields.Many2one(comodel_name='izi.analysis.metric', string='Metric', ondelete='cascade')
    dimension_id = fields.Many2one(comodel_name='izi.analysis.dimension', string='Dimension', ondelete='cascade')
    field_format = fields.Selection(string='Field Format', related='dimension_id.field_format')
    field_calculation = fields.Selection(string='Field Calculation', related='metric_id.calculation')
    sort = fields.Selection(string='Sort', selection=[
        ('asc', 'Ascending'),
        ('desc', 'Descending'),
    ], default='asc', required=True)

    @api.model
    def create(self, vals):
        analysis_id = self.env['izi.analysis'].browse(vals.get('analysis_id'))
        for dimension in analysis_id.dimension_ids:
            if dimension.field_id.id == vals.get('field_id'):
                vals['dimension_id'] = dimension.id
                break
        for metric in analysis_id.metric_ids:
            if metric.field_id.id == vals.get('field_id'):
                vals['metric_id'] = metric.id
                break
        res = super(IZIAnalysisSort, self).create(vals)
        return res
