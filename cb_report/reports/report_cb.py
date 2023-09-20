from tracemalloc import start
from odoo import models
from odoo.tools.misc import xlwt
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import re

# This code is for CBReport 

class CBXlsx(models.AbstractModel):
    _name = 'report.report_cbreport_xlsx'
    _inherit = 'report.report_xlsx.abstract'


    def generate_xlsx_report(self, workbook, data, items):       
        headers = ["BL NO", "Job Ref No","Job Type", "40FT", "20FT", "CBM", "KG", "ITEM DESCRIPTION", "SHIPPING LINE", "TERMINAL", "JOB DYNAMICS", "ATA", "TDO Date", "Delivery completion Date", "Final Destination", "Complete Doc. Received", "Duty", "Shipping charge", "Terminal Charge ", "NAFDAC",
                   "SON", "Agency", "Transportation", "Others", "Total Cost(N)", "Duty", "Shipping charge", "Terminal Charge ", "NAFDAC", "Agency", "Transportation", "Others", "Invoice Value(N)", "VAT(N)", "Total Invoice Value(N)", "Paid(N)", "WHT(N)", "Unpaid(N)", "Total Profit(N)", "COMMENT", "DGPATEL"]
        sheet = workbook.add_worksheet("CBReport")
        cell_format = workbook.add_format(
            {"font_size": 8, "border": True, "align": 'center'})
        header_format = workbook.add_format(
            {"bold": True, "font_size": 8, "border": True, "align": 'left', })
        sheet.merge_range(
            0, 0, 0, 14, 'INVOICE SUBMISSION TRACKING REPORT - SPRINGFIELD AGRO', header_format)
        sheet.merge_range(
            0, 15, 0, 23, 'EXPENSE CENTRES IN NAIRA(summation of inventory items in analytic/when amount double clicks it drills down to details/breakdown', header_format)
        sheet.merge_range(0, 24, 0, 36, 'INVOICE CENTRES IN NAIRA/DOLLAR/EURO/POUNDS(summation of inventory items and all income lines in validated invoice reporting in analytic/when amount double clicks it drills down to details/breakdown', header_format)
        sheet.merge_range(0, 37, 0, 38, 'Profile Section', header_format)
        row = 1
        column = 0
        for i in headers:
            sheet.write(row,column,i,header_format)
            sheet.set_column(0,column,15)
            column+=1
        project_data = self.env['project.project'].search([])
        final_row = ''
        sum_feet_forty = 0
        sum_feet_twenty = 0
        new_row = 1
        for pro in project_data:
            print ('___ pro.project_product_duty : ', pro.project_product_duty);
            new_row+=1
            sheet.write(new_row,0,pro.bol_awb_ref,cell_format)
            sheet.write(new_row,1,pro.job_refs,cell_format)
            sheet.write(new_row,2,pro.type_id.name,cell_format)
            sheet.write(new_row,3,pro.feet_forty,cell_format)
            sheet.write(new_row,4,pro.feet_twenty,cell_format)
            sheet.write(new_row,5,pro.cbm,cell_format)
            sheet.write(new_row,6,pro.kg,cell_format)
            item_desc = ''
            for i in pro.project_schedule_items_ids:
                item_desc+=i.product_id.name
                print ('___ item_desc : ', item_desc);
            sheet.write(new_row,7,str(item_desc),cell_format)
            sheet.write(new_row,8,pro.shipping_line,cell_format)
            sheet.write(new_row,9,pro.terminal,cell_format)
            sheet.write(new_row,10,pro.project_categ_id.name,cell_format)
            format2 = workbook.add_format({'num_format': 'dd/mm/yy' or ''})
            sheet.write(new_row,11,pro.ata or '',format2)
            sheet.write(new_row,12,pro.job_tdo or '',format2)
            sheet.write(new_row,13,pro.date_delivery_complete or '',format2)
            sheet.write(new_row,14,pro.dest_port,cell_format)
            no_tag = re.compile('<.*?>')
            new_description = re.sub(no_tag,'',pro.description)
            sheet.write(new_row,39,new_description,cell_format)
            final_row = str(new_row)
            sum_feet_forty += pro.feet_forty
            sum_feet_twenty += pro.feet_twenty

        again_new_row = int(final_row) + 2
        sheet.write(again_new_row,3,sum_feet_forty,cell_format)
        sheet.write(again_new_row,4,sum_feet_twenty,cell_format)