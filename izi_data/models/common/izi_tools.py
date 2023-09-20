# -*- coding: utf-8 -*-
import pandas
import requests
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import io
from io import StringIO, BytesIO
import logging
import ast
import json
from psycopg2 import extensions
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

_logger = logging.getLogger(__name__)

class IZITools(models.TransientModel):
    _name = 'izi.tools'

    @api.model
    def lib(self, key):
        lib = {
           'pandas': pandas,
           'json': json,
           'requests': requests, 
           'datetime': datetime,
           'timedelta': timedelta,
           'BeautifulSoup': BeautifulSoup,
        }
        if key not in lib:
            raise UserError('Library Not Found')
        return lib[key]
    
    @api.model
    def alert(self, message):
        raise UserError(message)

    @api.model
    def log(self, message):
        _logger.info('IZI_TOOLS_LOGGER > ' + message)

    @api.model
    def literal_eval(self, data):
        return ast.literal_eval(data)
    
    @api.model
    def query_insert(self, table_name, data, return_id=False):
        if type(data) is not dict:
            raise UserError('Data must be in dictionary!')
        insert_query = 'INSERT INTO %s (%s) VALUES %s'
        if return_id:
            insert_query += ' RETURNING id'
        insert_query = self.env.cr.mogrify(insert_query, (extensions.AsIs(table_name), extensions.AsIs(
            ','.join(data.keys())), tuple(data.values())))
        self.env.cr.execute(insert_query)
        new_id = False
        if return_id:
            new_id = self.env.cr.fetchone()[0]
        return new_id
    
    @api.model
    def query_check(self, query):
        self.env.cr.execute(query)
        res = self.env.cr.dictfetchall()
        raise UserError('''
            Total Rows: %s
            Query Results:
            
            %s
        ''' % (len(res), str(res)))
    
    @api.model
    def query_fetch(self, query):
        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()
    
    @api.model
    def query_execute(self, query, check=False):
        if 'UPDATE' in query.upper() or 'DELETE' in query.upper():
            if 'WHERE' not in query.upper():
                raise UserError('YOUR QUERY DO NOT HAVE WHERE CLAUSE. IT IS VERY DANGEROUS!')
        self.env.cr.execute(query)
        if check:
            res = self.env.cr.dictfetchall()
            raise UserError('''
                Total Rows: %s
                Query Results:
                
                %s
            ''' % (len(res), str(res)))

    @api.model
    def requests(self, method, url, headers={}, data={}):
        response = requests.request(method, url=url, headers=headers, data=data)
        return response

    @api.model
    def requests_io(self, method, url, headers={}, data={}):
        response = requests.request(method, url=url, headers=headers, data=data)
        return io.StringIO(response.content.decode('utf-8'))
    
    @api.model
    def read_csv(self, url, **kwargs):
        data = []
        try:
            df = pandas.read_csv(
                url,
                **kwargs
            )
            data = df.to_dict('records')
        except Exception as e:
            raise UserError(str(e))
        return data
    
    @api.model
    def read_excel(self, url, **kwargs):
        data = []
        try:
            df = pandas.read_excel(
                url,
                **kwargs
            )
            data = df.to_dict('records')
        except Exception as e:
            raise UserError(str(e))
        return data

    @api.model
    def read_attachment(self, name, date=False, **kwargs):
        data = []
        domain = [('name', '=', name)]
        if date:
            domain.append(('table_date', '=', date))
        attachment = self.env['ir.attachment'].search(domain, limit=1)
        if not attachment:
            raise UserError('Attachment Not Found')
        try:
            if attachment.mimetype == 'application/vnd.ms-excel':
                df = pandas.read_csv(BytesIO(attachment.raw), encoding="latin1")
            elif attachment.mimetype == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
                df = pandas.read_excel(BytesIO(attachment.raw))
            data = df.to_dict('records')
        except Exception as e:
            raise UserError(str(e))
        return data

    @api.model
    def read_google_spreadsheet(self, gsheetid, gsheetname=''):
        try:
            gsheet_url = "https://docs.google.com/spreadsheets/d/{}/gviz/tq?tqx=out:csv&sheet={}".format(
                gsheetid, gsheetname)
            df = pandas.read_csv(gsheet_url)
            data = df.to_dict('records')
        except Exception as e:
            raise UserError(str('Something wrong from your google spreadsheet.\n\nError Details:\n%s' % e))
        return data
