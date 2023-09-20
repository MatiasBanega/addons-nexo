# -*- coding: utf-8 -*-
# Copyright 2022 IZI PT Solusi Usaha Mudah
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.safe_eval import safe_eval
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class IZIAnalysis(models.Model):
    _inherit = 'izi.analysis'

    # Visual Type. Will be added on other modules.
    visual_type_id = fields.Many2one(comodel_name='izi.visual.type', string='Visual Type',
                                     default=lambda self: self.get_visual_type_table())
    analysis_visual_config_ids = fields.One2many(
        comodel_name='izi.analysis.visual.config', inverse_name='analysis_id', string='Analysis Visual Config')

    @api.model
    def create(self, vals):
        rec = super(IZIAnalysis, self).create(vals)
        # Set Default Metric
        if self._context.get('by_user') and not rec.metric_ids:
            Field = self.env['izi.table.field']
            metric_field = Field.search([('field_type', 'in', ('numeric', 'number')),
                                        ('table_id', '=', rec.table_id.id)], limit=1)
            if metric_field:
                rec.metric_ids = [(0, 0, {
                    'field_id': metric_field.id,
                    'calculation': 'count',
                })]
        return rec

    def write(self, vals):
        res = super(IZIAnalysis, self).write(vals)
        # Set Default Metric
        for analysis in self:
            if self._context.get('by_user') and not analysis.metric_ids:
                Field = self.env['izi.table.field']
                metric_field = Field.search([('field_type', 'in', ('numeric', 'number')),
                                            ('table_id', '=', analysis.table_id.id)], limit=1)
                if metric_field:
                    analysis.metric_ids = [(0, 0, {
                        'field_id': metric_field.id,
                        'calculation': 'count',
                    })]
        return res

    def get_visual_type_table(self):
        visual_type_id = False
        visual_type_table = self.env['izi.visual.type'].search([('name', '=', 'table')], limit=1)
        if visual_type_table:
            visual_type_id = visual_type_table[0].id
        return visual_type_id

    def ui_get_analysis_info(self):
        self.ensure_one()
        res = {
            'visual_type': self.visual_type_id.name,
            'metrics': [],
            'fields_for_metrics': [],
            'dimensions': [],
            'fields_for_dimensions': [],
            'sorts': [],
            'fields_for_sorts': [],
            'filters': [],
            'fields_for_filters': [],
            'limit': self.limit,
            'filter_operators': [],
        }
        # Metrics and Dimensions
        for metric in self.metric_ids:
            res['metrics'].append({
                'id': metric.field_id.id,
                'name': metric.field_id.name,
                'field_type': metric.field_id.field_type,
                'calculation': metric.calculation,
                'metric_id': metric.id,
                'sort': metric.sort,
            })
            res['fields_for_sorts'].append({
                'id': metric.field_id.id,
                'name': metric.field_id.name,
                'field_type': metric.field_id.field_type,
            })
        for dimension in self.dimension_ids:
            res['dimensions'].append({
                'id': dimension.field_id.id,
                'name': dimension.field_id.name,
                'field_type': dimension.field_id.field_type,
                'dimension_id': dimension.id,
                'field_format': dimension.field_format,
                'sort': dimension.sort,
            })
            res['fields_for_sorts'].append({
                'id': dimension.field_id.id,
                'name': dimension.field_id.name,
                'field_type': dimension.field_id.field_type,
            })
        # Sorts
        for sort in self.sort_ids:
            res['sorts'].append({
                'id': sort.field_id.id,
                'name': sort.field_id.name,
                'field_type': sort.field_id.field_type,
                'sort_id': sort.id,
                'field_format': sort.field_format,
                'field_calculation': sort.field_calculation,
                'sort': sort.sort,
            })
        # Filters
        for filter_id in self.filter_ids:
            res['filters'].append({
                'id': filter_id.field_id.id,
                'name': filter_id.field_id.name,
                'field_type': filter_id.field_id.field_type,
                'filter_id': filter_id.id,
                'operator_id': filter_id.operator_id.id,
                'condition': filter_id.condition,
                'value': filter_id.value,
            })
        # Filter Operators
        filter_operators = self.env['izi.analysis.filter.operator'].search([('source_type', '=', self.source_id.type)])
        for operator in filter_operators:
            res['filter_operators'].append({
                'operator_id': operator.id,
                'operator_name': operator.name,
            })
        for field in self.table_id.field_ids:
            if field.field_type in ('numeric', 'number'):
                res['fields_for_metrics'].append({
                    'id': field.id,
                    'name': field.name,
                    'field_type': field.field_type,
                })
            elif field.field_type not in ('numeric', 'number'):
                res['fields_for_dimensions'].append({
                    'id': field.id,
                    'name': field.name,
                    'field_type': field.field_type,
                })
            res['fields_for_filters'].append({
                'id': field.id,
                'name': field.name,
                'field_type': field.field_type,
            })
        return res

    def ui_get_filter_info(self):
        self.ensure_one()
        res = {
            'filters': [],
            'fields': {
                'string_search': [],
                'date_range': [],
                'date_format': [],
            },
        }
        for filter in self.filter_temp_ids:
            res['filters'].append({
                'filter_id': filter.id,
                'type': filter.type,
                'id': filter.field_id.id,
                'name': filter.field_id.name,
                'field_name': filter.field_id.field_name,
            })
        for field in self.table_id.field_ids:
            if field.field_type in ('string'):
                res['fields']['string_search'].append({
                    'id': field.id,
                    'name': field.name,
                    'field_type': field.field_type,
                })
            elif field.field_type in ('date', 'datetime'):
                res['fields']['date_range'].append({
                    'id': field.id,
                    'name': field.name,
                    'field_type': field.field_type,
                })
                res['fields']['date_format'].append({
                    'id': field.id,
                    'name': field.name,
                    'field_type': field.field_type,
                })
        return res

    def ui_add_filter_temp_by_field(self, field_id, type):
        self.ensure_one()
        for filter in self.filter_temp_ids:
            if filter.type == type:
                filter.unlink()
        if field_id > 0:
            self.filter_temp_ids = [(0, 0, {
                'field_id': field_id,
                'type': type,
            })]

    def ui_remove_metric(self, metric_id):
        self.ensure_one()
        self.metric_ids = [(2, metric_id)]

    def ui_add_metric_by_field(self, field_id):
        self.ensure_one()
        for metric in self.metric_ids:
            if metric.field_id.id == field_id:
                return False
        self.metric_ids = [(0, 0, {
            'field_id': field_id,
            'calculation': 'sum',
        })]

    def ui_remove_dimension(self, dimension_id):
        self.ensure_one()
        self.dimension_ids = [(2, dimension_id)]

    def ui_remove_sort(self, sort_id):
        self.ensure_one()
        self.sort_ids = [(2, sort_id)]

    def ui_remove_filter(self, filter_id):
        self.ensure_one()
        self.filter_ids = [(2, filter_id)]

    def ui_add_dimension_by_field(self, field_id):
        self.ensure_one()
        for dimension in self.dimension_ids:
            if dimension.field_id.id == field_id:
                return False
        if self.visual_type_id.name == 'table' or len(self.dimension_ids) == 0 or (len(self.dimension_ids) == 1 and len(self.metric_ids) <= 1):
            self.dimension_ids = [(0, 0, {
                'field_id': field_id,
            })]
        elif len(self.dimension_ids) >= 1:
            dimension_id = self.dimension_ids[0].id
            self.dimension_ids = [
                (2, dimension_id),
                (0, 0, {
                    'field_id': field_id,
                }),
            ]

    def ui_add_sort_by_field(self, field_id):
        self.ensure_one()
        for sort in self.sort_ids:
            if sort.field_id.id == field_id:
                return False
        self.sort_ids = [
            (0, 0, {
                'field_id': field_id
            }),
        ]

    def ui_add_filter_by_field(self, data={}):
        self.ensure_one()
        try:
            if data.get('field_id', False) in [None, False]:
                raise ValidationError('Please input Field!')
            elif data.get('condition', False) in [None, False]:
                raise ValidationError('Please input Operator!')
            elif data.get('operator_id', False) in [None, False]:
                raise ValidationError('Please input Operator!')
            elif data.get('value', False) in [None, False]:
                raise ValidationError('Please input Value!')
            self.filter_ids = [
                (0, 0, {
                    'field_id': data.get('field_id'),
                    'operator_id': int(data.get('operator_id')),
                    'condition': data.get('condition'),
                    'value': data.get('value'),
                }),
            ]
        except Exception as e:
            raise ValidationError(str(e))

    def ui_update_filter_by_field(self, data={}):
        self.ensure_one()
        try:
            if data.get('filter_id', False) in [None, False]:
                raise ValidationError('Please input Filter!')
            elif data.get('condition', False) in [None, False]:
                raise ValidationError('Please input Operator!')
            elif data.get('operator_id', False) in [None, False]:
                raise ValidationError('Please input Operator!')
            elif data.get('value', False) in [None, False]:
                raise ValidationError('Please input Value!')
            self.filter_ids = [
                (1, data.get('filter_id'), {
                    'field_id': data.get('field_id'),
                    'operator_id': int(data.get('operator_id')),
                    'condition': data.get('condition'),
                    'value': data.get('value'),
                }),
            ]
        except Exception as e:
            raise ValidationError(str(e))
    
    def ui_get_view_parameters(self, kwargs):
        self.ensure_one()
        domain = []
        date_field = self.date_field_id
        res = {
            'name': self.name,
            'model': self.model_id.model,
            'domain': self.domain,
        }
        if self.kpi_id and self.kpi_id.model_id:
            res['model'] = self.kpi_id.model_id.model
            res['domain'] = self.kpi_id.domain
            date_field = self.kpi_id.date_field_id
        # Calculate Domain
        if res.get('domain'):
            domain = safe_eval(res.get('domain'))
        if kwargs.get('filters'):
            # Check Default Date Filter In Analysis If Filters Empty
            if date_field and not kwargs.get('filters').get('date_format'):
                if self.date_format:
                    kwargs['filters']['date_format'] = self.date_format
                    if self.date_format == 'custom' and (self.start_date or self.end_date):
                        kwargs['filters']['date_range'] = [self.start_date, self.end_date]
            # Process Date Filter
            if date_field and kwargs.get('filters').get('date_format'):
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
                if date_field.field_type == 'date':
                    if start_date:
                        domain.append((date_field.field_name, '>=', start_date))
                    if end_date:
                        domain.append((date_field.field_name, '<=', end_date))
                if date_field.field_type == 'datetime':
                    if start_datetime:
                        domain.append((date_field.field_name, '>=', start_datetime))
                    if end_datetime:
                        domain.append((date_field.field_name, '<=', end_datetime))
        res['domain'] = domain
        return res

    @api.model
    def ui_get_all(self, args={}):
        res = []
        domain = []
        if args.get('category_id'):
            domain.append(('category_id', '=', args.get('category_id')))
        if args.get('visual_type_id'):
            domain.append(('visual_type_id', '=', args.get('visual_type_id')))
        if args.get('keyword'):
            domain.append(('name', 'ilike', args.get('keyword')))
        all_analysis = self.search(domain)
        for analysis in all_analysis:
            res.append({
                'id': analysis.id,
                'name': analysis.name,
                'table_id': analysis.table_id.id,
                'table_name': analysis.table_id.name,
                'source_id': analysis.table_id.source_id.id,
                'source_name': analysis.table_id.source_id.name,
                'visual_type': analysis.visual_type_id.name,
                'visual_type_icon': analysis.visual_type_id.icon,
                'category_name': analysis.category_id.name,
            })
        return res

    def ui_execute_query(self, table_id, query):
        self.ensure_one()
        res = {
            'data': [],
            'message': False,
            'status': 500,
        }
        try:
            # Get Query Field Names
            test_result = self.table_id.ui_test_query(query)
            test_data = test_result['data']
            test_field_names = []
            if test_data:
                test_data = test_data[0]
                for key in test_data:
                    test_field_names.append(key)
            # Delete Fields That Not In Query Field Names
            Metric = self.env['izi.analysis.metric']
            Dimension = self.env['izi.analysis.dimension']
            # Get Fields
            for field in self.table_id.field_ids:
                if field.field_name not in test_field_names:
                    # Delete Metrics
                    metrics = Metric.search([('field_id', '=', field.id)])
                    metrics.unlink()
                    # Delete Dimensions
                    dimensions = Dimension.search([('field_id', '=', field.id)])
                    dimensions.unlink()
                    # Delete Field
                    field.unlink()
            # Update Table
            self.table_id = table_id
            self.table_id.db_query = query
            # Execute Query
            self.table_id.get_table_fields()
            # Results
            res['data'] = test_data
            res['message'] = 'Success'
            res['status'] = 200
        except Exception as e:
            self.env.cr.rollback()
            res['message'] = str(e)
            res['status'] = 500
        return res

    def save_analysis_visual_type(self, visual_type):
        self.ensure_one()
        vt = self.env['izi.visual.type'].search([('name', '=', visual_type)], limit=1)
        if vt:
            self.visual_type_id = vt.id
            self.analysis_visual_config_ids = False
        return True

    def save_analysis_visual_config(self, analysis_visual_config):
        self.ensure_one()
        exist_visual_config_by_id = {}
        for exist_visual_config in self.analysis_visual_config_ids:
            exist_visual_config_by_id[exist_visual_config.id] = exist_visual_config
        for visual_config in analysis_visual_config:
            if exist_visual_config_by_id.get(visual_config.get("id")) is not None:
                exist_visual_config_by_id.get(visual_config.get("id")).write(visual_config)
                exist_visual_config_by_id.pop(visual_config.get("id"))
            else:
                self.analysis_visual_config_ids = [(0, 0, visual_config)]
        for exist_visual_config in exist_visual_config_by_id:
            exist_visual_config_by_id.get(exist_visual_config).unlink()
        return True

    def get_analysis_data_dashboard(self, **kwargs):
        self.ensure_one()

        max_dimension = False
        if self.visual_type_id.name != 'table':
            if len(self.metric_ids) > 1:
                max_dimension = 1
            else:
                max_dimension = 2

        kwargs.update({'max_dimension': max_dimension})

        result = self.get_analysis_data(**kwargs)

        visual_config_values = {}
        for analysis_visual_config in self.analysis_visual_config_ids:
            config_type = analysis_visual_config.visual_config_id.config_type
            config_value = analysis_visual_config.string_value
            if config_type == 'input_number':
                config_value = int(config_value)
            elif config_type == 'toggle':
                config_value = True if config_value == 'true' else False
            elif 'selection' in config_type:
                value_type = analysis_visual_config.visual_config_value_id.value_type
                if value_type == 'number':
                    config_value = int(config_value)
            visual_config_values[analysis_visual_config.visual_config_id.name] = config_value
        result['visual_config_values'] = visual_config_values

        result['visual_type'] = self.visual_type_id.name
        result['analysis_name'] = self.name

        # Multi Dimensions Transform Into Multi Metrics
        # Works Only For Two Dimensions & Bar Line Chart
        if 'line' in result['visual_type'] or 'bar' in result['visual_type'] or 'row' in result['visual_type']:
            if len(result['dimensions']) > 1:
                # 1. Get First Dimension, Second Dimension
                if len(result['dimensions']) > 1:
                    first_dimension = result['dimensions'][0]
                    second_dimension = result['dimensions'][1]
                # 2. Get All Possible Values For Second Dimension
                second_dimension_values = []
                for rd in result['data']:
                    if rd[second_dimension] not in second_dimension_values:
                        second_dimension_values.append(str(rd[second_dimension]))
                # 3. Create New Metrisc With Second Dimension Values
                # Looping Stored New Metrics Data By First Dimension Dictionary
                new_metrics = []
                new_dimensions = [first_dimension]
                new_fields = [first_dimension]
                res_data_by_first_dimension = {}
                for rd in result['data']:
                    if rd[first_dimension] not in res_data_by_first_dimension:
                        res_data_by_first_dimension[rd[first_dimension]] = {}
                    for rm in result['metrics']:
                        for sdv in second_dimension_values:
                            # Too Long
                            # new_metric = '%s %s' % (rm, sdv)
                            new_metric = sdv
                            if new_metric not in new_metrics:
                                new_metrics.append(new_metric)
                            if new_metric not in new_fields:
                                new_fields.append(new_metric)
                            if new_metric not in res_data_by_first_dimension[rd[first_dimension]]:
                                res_data_by_first_dimension[rd[first_dimension]][new_metric] = 0
                            if sdv == rd[second_dimension]:
                                value = rd[rm]
                                res_data_by_first_dimension[rd[first_dimension]][new_metric] = value
                # 4. Loop Again And Redefined new_data, new_metrics, new_dimensions
                new_data = []
                for fdv in res_data_by_first_dimension:
                    nd = {}
                    nd[first_dimension] = fdv
                    for nm in new_metrics:
                        nd[nm] = res_data_by_first_dimension[fdv][nm]
                    new_data.append(nd)
                # 5. Set New Result
                result['data'] = new_data
                result['metrics'] = new_metrics
                result['dimensions'] = new_dimensions
                result['fields'] = new_fields
        return result

    # Inherit Get Data And Reformat For AmChart
    def get_analysis_data_amchart(self):
        self.ensure_one()
        result = self.get_analysis_data()
        if len(result.get('metrics')) == 1 and len(result.get('dimensions')) == 2:
            amchart_data = []
            amchart_dimension_values = []
            amchart_dimension_to_metric_values = []
            amchart_metric = result.get('metrics')[0]
            amchart_dimension = result.get('dimensions')[0]
            amchart_dimension_to_metric = result.get('dimensions')[1]
            matric_value_by_dimension = {}

            for data in result.get('data'):
                if data.get(amchart_dimension) not in amchart_dimension_values:
                    amchart_dimension_values.append(data.get(amchart_dimension))
                if data.get(amchart_dimension_to_metric) not in amchart_dimension_to_metric_values:
                    amchart_dimension_to_metric_values.append(data.get(amchart_dimension_to_metric))
                matric_value_by_dimension['%s,%s' % (data.get(amchart_dimension), data.get(
                    amchart_dimension_to_metric))] = data.get(amchart_metric)

            for dimension in amchart_dimension_values:
                amchart_data_dict = {}
                amchart_data_dict[amchart_dimension] = dimension
                for dimension_to_metric in amchart_dimension_to_metric_values:
                    matric_value = matric_value_by_dimension.get('%s,%s' % (dimension, dimension_to_metric))
                    if matric_value is None:
                        matric_value = 0
                    amchart_data_dict[dimension_to_metric] = matric_value
                amchart_data.append(amchart_data_dict)

            result['data'] = amchart_data

        if 'test_analysis_amchart' not in self._context:
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
