from tracemalloc import start
from odoo import models
from odoo.tools.misc import xlwt
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import re

class WaybillXlsx(models.AbstractModel):
    _name = 'report.customize_vpcs.report_waybill_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, items):
        print('Items :', items)
        headers = ["BL NO", "Job Ref No", "40FT", "20FT", "CBM", "KG", "ITEM DESCRIPTION", "SHIPPING LINE", "TERMINAL", "JOB DYNAMICS", "ATA", "TDO Date", "Delivery completion Date", "Final Destination", "Complete Doc. Received", "Duty", "Shipping charge", "Terminal Charge ", "NAFDAC",
                   "SON", "Agency", "Transportation", "Others", "Total Cost(N)", "Duty", "Shipping charge", "Terminal Charge ", "NAFDAC", "Agency", "Transportation", "Others", "Invoice Value(N)", "VAT(N)", "Total Invoice Value(N)", "Paid(N)", "WHT(N)", "Unpaid(N)", "Total Profit(N)", "COMMENT"]
        sheet = workbook.add_worksheet("waybill")
        cell_format = workbook.add_format(
            {"bold": True, "font_size": 8, "border": True, "align": 'left'})
        header_format = workbook.add_format(
            {"bold": True, "font_size": 8, "border": True, "align": 'center', })
        sheet.merge_range(
            0, 0, 0, 14, 'INVOICE SUBMISSION TRACKING REPORT - SPRINGFIELD AGRO', cell_format)
        sheet.merge_range(
            0, 15, 0, 23, 'EXPENSE CENTRES IN NAIRA(summation of inventory items in analytic/when amount double clicks it drills down to details/breakdown', cell_format)
        sheet.merge_range(0, 24, 0, 36, 'INVOICE CENTRES IN NAIRA/DOLLAR/EURO/POUNDS(summation of inventory items and all income lines in validated invoice reporting in analytic/when amount double clicks it drills down to details/breakdown', cell_format)
        sheet.merge_range(0, 37, 0, 38, 'Profile Section', cell_format)
        row = 1
        column = 0
        for i in headers:
            sheet.write(row,column,i,header_format)
            sheet.set_column(0,column,15)
            column+=1
        for item in items:
            pass

class BargedXlsx(models.AbstractModel):
    _name = 'report.customize_vpcs.report_barged_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, items):
        print('Items :', items)
        headers = ["S/N",'DATE','CONT NO','BL NO','SIZE','CLIENT','DESTINATION','FILE NO','WEIGHT','LINER']
        sheet = workbook.add_worksheet("Barged_Tracking")
        header_format = workbook.add_format(
            {"bold": True, "font_size": 12, "border": True, "align": 'center',"bg_color":"#000080","color":'white'})
        cell_format = workbook.add_format(
            {"font_size": 8, "border": True, "align": 'center'})
        row = 0
        column = 0
        for i in headers:
            sheet.write(row,column,i,header_format)
            column+=1
        sr_no = 1
        new_row = 0
        for j in items:
            new_row+=1
            date_time = datetime.strptime(j.create_date.strftime("%Y-%m-%d"), '%Y-%m-%d')
            sheet.write(new_row,0,sr_no,cell_format)
            sheet.write_datetime(new_row,1,date_time,cell_format)
            sheet.write(new_row,2,"",cell_format)
            sheet.set_column(2,2,15)
            sheet.write(new_row,3,j.project_id.bol_awb_ref,cell_format)
            sheet.set_column(3,3,16)
            sheet.write(new_row,4,j.project_id.items_total_size,cell_format)
            sheet.write(new_row,5,j.project_id.partner_id.name,cell_format)
            sheet.set_column(5,5,17)
            sheet.write(new_row,6,"",cell_format)
            sheet.set_column(6,6,30)
            sheet.write(new_row,7,"",cell_format)
            sheet.set_column(7,7,15)
            sheet.write(new_row,8,j.project_id.items_total_weight,cell_format)
            sheet.write(new_row,9,j.project_id.has_job_liner,cell_format)
            sr_no+=1

# This code is for operation report

class OperationXlsx(models.AbstractModel):
    _name = 'report.customize_vpcs.report_operation_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, items):
        print('Items :', items)
        headers = ["S/N",'COMMENTS','STAGE','CLIENT NAME','Dynamics','Pre-alert Date','File ref','20 FT','40 FT','BL/AWB NUMBER','SHIPPING LINE','TERMINAL','ATA','CONT-Transfer','PAAR Recieved','ASSES DATE','Duty Received','Original Shipping Doc rec','1ST STAMPING','2ND STAMPING','TDO DATE','CLEARING AGENT','DAYS IN PORT','MAJOR CAUSE OF DELAY']
        sheet = workbook.add_worksheet("Operation_Report")
        header_format = workbook.add_format(
            {"bold": True, "font_size": 12, "border": True, "align": 'center',"bg_color":"#DCDCDC","color":'black'})
        cell_format = workbook.add_format(
            {"font_size": 8, "border": True, "align": 'center'})
        row = 0
        column = 0
        for i in headers:
            sheet.write(row,column,i,header_format)
            column+=1
        sr_no = 1
        new_row = 0
        for j in items:
            new_row+=1
            sheet.write(new_row,0,sr_no,cell_format)
            no_tag = re.compile('<.*?>')
            new_description = re.sub(no_tag,'',j.description if j.description else '')
            sheet.write(new_row,1,new_description,cell_format)
            sheet.write(new_row,2,j.sn_state,cell_format)
            sheet.write(new_row,3,j.client_name.name,cell_format)
            sheet.write(new_row,4,j.project_categ_id.name,cell_format)
            format2 = workbook.add_format({'num_format': 'dd/mm/yy'})            
            sheet.write(new_row,5,j.pre_alert_date or '',format2)
            sheet.write(new_row,6,'',cell_format)
            sheet.write(new_row,7,j.feet_forty,cell_format)
            sheet.write(new_row,8,j.feet_twenty,cell_format)
            sheet.write(new_row,9,j.bol_awb_ref,cell_format)
            sheet.write(new_row,10,j.shipping_line,cell_format)
            sheet.write(new_row,11,j.terminal,cell_format)
            sheet.write(new_row,12,j.ata,cell_format)
            sheet.write(new_row,13,j.container_transfer or '',format2)
            sheet.write(new_row,14,j.paar_received or '',format2)
            sheet.write(new_row,15,j.duty_assesment or '',format2)
            sheet.write(new_row,16,j.duty_received or '',format2)
            sheet.write(new_row,17,j.original_copy_received or '',format2)
            sheet.write(new_row,18,j.nafdac_1_stamp_date or '',format2)
            sheet.write(new_row,19,j.nafdac_2_stamp_date or '',format2)
            sheet.write(new_row,20,j.job_tdo or '',format2)
            sheet.write(new_row,21,j.clearing_agent_id.name or '',cell_format)
            sheet.write(new_row,22,j.days_in_port if j.days_in_port else '',cell_format)
            sheet.write(new_row,23,j.major_cause_of_delay or '',cell_format)
            sr_no+=1