
import base64
import os
from datetime import datetime
from datetime import date
from datetime import *
from io import BytesIO , StringIO
from odoo.exceptions import except_orm, Warning, RedirectWarning, UserError, ValidationError

import xlsxwriter
from PIL import Image as Image
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from xlsxwriter.utility import xl_rowcol_to_cell



class payrollreportexcelwiz(models.TransientModel):
    _name = 'payroll.report.wiz'
    
    from_date = fields.Date('From Date', required=True)
    date_end= fields.Date('To Date', required=True)
    report = fields.Many2one("payroll.report", "Payroll Report", required=True)
    show_logo  = fields.Boolean(
        string='Show Company Logo',default=True)
    filter = fields.Selection(
        string='Filter',
        selection=[('all', 'All'),
                   ('employee', 'Employee'),
                   ('company','Company'),
                   ('department', 'Department'),],
        required=True,default="all" )
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',)
    department_id = fields.Many2one(
        comodel_name='hr.department',
        string='Department',)
    company_id = fields.Many2one('res.company', default=lambda self: self.env['res.company']._company_default_get(),
                              string="Company")

    #to get salary rules names
    def get_rules(self):
        vals = []
        list = []
        for rule in self.report.rule_ids:
            list = [rule.name, rule.code]
            vals.append(list)
        return vals



    def get_item_data(self):
        font_color = '#000000'
        file_name = _('Payroll Report.xlsx')
        fp = BytesIO()

        workbook = xlsxwriter.Workbook(fp)
        heading_format = workbook.add_format({'align': 'center',
                                              'valign': 'vcenter',
                                              'font_color': font_color,
                                              'bold': True, 'size': 14})

        cell_text_format_n = workbook.add_format({'align': 'center',
                                                  'font_color': font_color,
                                                  'bold': True, 'size': 9,
                                                  })
        cell_text_format = workbook.add_format({'align': 'left',
                                                'font_color': font_color,
                                                'bold': True, 'size': 9,
                                                })

        cell_text_format.set_border()
        cell_text_format_new = workbook.add_format({'align': 'left',
                                                    'font_color': font_color,
                                                    'size': 9,
                                                    })
        cell_text_format_new.set_border()
        cell_number_format = workbook.add_format({'align': 'right',
                                                  'font_color': font_color,
                                                  'bold': False, 'size': 9,
                                                  'num_format': '#,###0.00'})
        cell_number_format.set_border()
        worksheet = workbook.add_worksheet('Payroll Report.xlsx')
        normal_num_bold = workbook.add_format({'bold': True, 'num_format': '#,###0.00', 'size': 9, })
        normal_num_bold.set_border()
        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 20)
        worksheet.set_column('G:G', 20)
        worksheet.set_column('H:H', 20)
        worksheet.set_column('I:I', 20)
        worksheet.set_column('J:J', 20)
        worksheet.set_column('K:K', 20)
        worksheet.set_column('L:L', 20)
        worksheet.set_column('M:M', 20)
        worksheet.set_column('N:N', 20)

        if self.from_date and self.date_end:
            if self.show_logo:
                img = self.env['res.company'].search([('id', '=', 1)])
                if img.logo:
                    buf_image = BytesIO(base64.b64decode(img.logo))
                    worksheet.insert_image('D4', 'buf_image.png', {'image_data': buf_image,
                                                                   'x_offset': 1,
                                                                   'y_offset': 1,
                                                                   'x_scale': 0.2,
                                                                   'y_scale': 0.2,
                                                                   'object_position': 2,
                                                                   })
            date_2 = datetime.strptime(str(self.date_end), '%Y-%m-%d').strftime('%Y-%m-%d')
            date_1 = datetime.strptime(str(self.from_date), '%Y-%m-%d').strftime('%Y-%m-%d')
            payroll_month = datetime.strptime(str(self.from_date), '%Y-%m-%d').strftime('%B')
            payroll_year = datetime.strptime(str(self.from_date), '%Y-%m-%d').strftime('%Y')
            worksheet.merge_range('C1:G3', 'Payroll For %s %s' % (payroll_month, payroll_year), heading_format)
            row = 3
            column = 0
            worksheet.write(row, 4, 'Date From', cell_text_format_n)
            worksheet.write(row, 5, date_1 or '')
            row += 1
            worksheet.write(row, 4, 'Date To', cell_text_format_n)
            worksheet.write(row, 5, date_2 or '')
            row += 1
            worksheet.write(row, 4, 'Company', cell_text_format_n)
            worksheet.write(row, 5, self.company_id.name or '')
            row += 2
            res = self.get_rules()
            worksheet.write(row, 0, 'Employee', cell_text_format)
            worksheet.write(row, 1, 'Department Name', cell_text_format)

            column = 2
            #to write salary rules names in the row
            for vals in res:
                worksheet.write(row, column, vals[0], cell_text_format)
                column += 1
            row = row + 1

            if self.filter == 'all':
                payslip_ids=self.env['hr.payslip'].search([('date_from','=',self.from_date),('date_to','=',self.date_end)])
            elif self.filter == 'employee':
                payslip_ids=self.env['hr.payslip'].search([('date_from','=',self.from_date),('date_to','=',self.date_end),('employee_id','=',self.employee_id.id)])
            elif self.filter == 'department':
                payslip_ids=self.env['hr.payslip'].search([('date_from','=',self.from_date),('date_to','=',self.date_end),('department_id','=',self.department_id.id)])
            elif self.filter == 'company':
                payslip_ids=self.env['hr.payslip'].search([('date_from','=',self.from_date),('date_to','=',self.date_end),('company_id','=',self.company_id.id)])

            if payslip_ids:
                for payslip in payslip_ids:
                    column = 0
                    worksheet.write(row, column, payslip.employee_id.name or '', cell_text_format_new)
                    column = column + 1
                    worksheet.write(row, column, payslip.employee_id.department_id.name or '', cell_text_format_new)
                    for vals in res:
                        column = column + 1
                        check = False
                        for line in payslip.line_ids:
                            if line.code == vals[1]:
                                check = True
                                amount = line.total
                        if check == True:
                            worksheet.write(row, column, amount, cell_number_format)
                        else:
                            worksheet.write(row, column, 0, cell_number_format)
                    row += 1

        worksheet.write(row, 0, 'Total', cell_text_format)
        column = 2
        for vals in res:
            total = 0.0
            for payslip in payslip_ids:
                    for line in payslip.line_ids:
                        if line.code == vals[1]:
                            total = total + line.total
            worksheet.write(row, column, total, normal_num_bold)
            column = column + 1

        workbook.close()
        file_download = base64.b64encode(fp.getvalue())
        fp.close()
        self = self.with_context(default_name=file_name, default_file_download=file_download)

        return {
            'name': 'payroll report Download',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'payroll.report.excel',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': self._context,
        }



class payroll_report_excel(models.TransientModel):
    _name = 'payroll.report.excel'

    name = fields.Char('File Name', size=256, readonly=True)
    file_download = fields.Binary('Download payroll', readonly=True)

