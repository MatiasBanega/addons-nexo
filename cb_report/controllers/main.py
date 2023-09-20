from odoo import http
from odoo.http import content_disposition, request
import io
import xlsxwriter
import re

class Custom_Quickbook_controller(http.Controller):

    @http.route('/project/excel_report', type="http", auth="public", website=True)
    def get_auth_code(self, **kwarg):
        response = request.make_response(
                    None,
                    headers=[
                        ('Content-Type', 'application/vnd.ms-excel'),
                        ('Content-Disposition', content_disposition('C&B Report' + '.xlsx'))
                    ]
                )
 
        # create workbook object from xlsxwriter library
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        headers = ["BL NO", "Job Ref No","Job Type", "40FT", "20FT", "CBM", "KG", "ITEM DESCRIPTION", "SHIPPING LINE", "TERMINAL", "JOB DYNAMICS", "ATA", "TDO Date", "Delivery completion Date", "Final Destination", "Complete Doc. Received", "Duty", "Shipping charge", "Terminal Charge ", "NAFDAC",
                   "SON", "Agency", "Transportation", "Others", "Total Cost(N)", "Duty Income", "Shipping charge", "Terminal Charge ", "NAFDAC", "Agency", "Transportation", "Others", "Invoice Value(N)", "VAT(N)", "Total Invoice Value(N)", "Paid(N)", "WHT(N)", "Unpaid(N)", "Total Profit(N)", "COMMENT"]
        sheet = workbook.add_worksheet("CBReport")
        cell_format = workbook.add_format(
            {"font_size": 8, "border": True, "align": 'center'})
        header_format = workbook.add_format(
            {"bold": True, "font_size": 8, "border": True, "align": 'left', })
        sheet.merge_range(
            0, 0, 0, 14, 'INVOICE SUBMISSION TRACKING REPORT - SPRINGFIELD AGRO', header_format)
        sheet.merge_range(
            0, 15, 0, 24, 'EXPENSE CENTRES IN NAIRA(summation of inventory items in analytic/when amount double clicks it drills down to details/breakdown', header_format)
        sheet.merge_range(0, 25, 0, 36, 'INVOICE CENTRES IN NAIRA/DOLLAR/EURO/POUNDS(summation of inventory items and all income lines in validated invoice reporting in analytic/when amount double clicks it drills down to details/breakdown', header_format)
        sheet.merge_range(0, 37, 0, 38, 'Profile Section', header_format)
        row = 1
        column = 0
        for i in headers:
            sheet.write(row,column,i,header_format)
            sheet.set_column(0,column,15)
            column+=1
        project_data = request.env['project.project'].search([('report_wizard_bool','=',True)])
        final_row = ''
        sum_feet_forty = 0
        sum_feet_twenty = 0
        new_row = 1
        for pro in project_data:
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
            sheet.write(new_row,7,str(item_desc),cell_format)
            sheet.write(new_row,8,pro.shipping_line,cell_format)
            sheet.write(new_row,9,pro.terminal,cell_format)
            sheet.write(new_row,10,pro.project_categ_id.name,cell_format)
            format2 = workbook.add_format({'num_format': 'dd/mm/yy' or ''})
            sheet.write(new_row,11,pro.ata or '',format2)
            sheet.write(new_row,12,pro.job_tdo or '',format2)
            sheet.write(new_row,13,pro.date_delivery_complete or '',format2)
            sheet.write(new_row,14,pro.dest_port,cell_format)
            sheet.write(new_row,16,pro.project_product_duty or 0.0,cell_format)
            sheet.write(new_row,17,pro.project_shipping_charge or 0.0,cell_format)
            sheet.write(new_row,18,pro.project_terminal_charge or 0.0,cell_format)
            sheet.write(new_row,19,pro.project_nafdac or 0.0,cell_format)
            sheet.write(new_row,20,pro.project_son or 0.0,cell_format)
            sheet.write(new_row,21,pro.project_agency or 0.0,cell_format)
            sheet.write(new_row,22,pro.project_transportation or 0.0,cell_format)
            sheet.write(new_row,23,pro.project_others or 0.0,cell_format)
            sheet.write(new_row,24,pro.lib_project_com or 0.0,cell_format)
            sheet.write(new_row,25,pro.customer_duty or 0.0,cell_format)
            sheet.write(new_row,26,pro.customer_shipping_charge or 0.0,cell_format)
            sheet.write(new_row,27,pro.customer_terminal_charge or 0.0,cell_format)
            sheet.write(new_row,28,pro.customer_nafdac or 0.0,cell_format)
            sheet.write(new_row,29,pro.customer_son or 0.0,cell_format)
            sheet.write(new_row,30,pro.customer_agency or 0.0,cell_format)
            sheet.write(new_row,31,pro.customer_transportation or 0.0,cell_format)
            sheet.write(new_row,32,pro.customer_others or 0.0,cell_format)
            sheet.write(new_row,32,pro.customer_untaxed_value or 0.0,cell_format)
            sheet.write(new_row,33,pro.customer_vat or 0.0,cell_format)
            sheet.write(new_row,34,pro.customer_total_invoice_value or 0.0,cell_format)
            sheet.write(new_row,35,pro.customer_invoice_paid or 0.0,cell_format)
            sheet.write(new_row,36,pro.wht or 0.0,cell_format)
            sheet.write(new_row,37,pro.customer_invoice_unpaid or 0.0,cell_format)
            sheet.write(new_row,38,pro.total_profit or 0.0,cell_format)
            # duty = 0
            # for j in pro.job_vendor_bill_ids.invoice_line_ids:
            #     duty+=j.price_subtotal
            # sheet.write(new_row,16,duty,cell_format)
            no_tag = re.compile('<.*?>')
            new_description = re.sub(no_tag,'',(pro.description) if pro.description else '')
            sheet.write(new_row,39,new_description,cell_format)
            final_row = str(new_row)
            sum_feet_forty += pro.feet_forty
            sum_feet_twenty += pro.feet_twenty

        again_new_row = int(final_row) + 2
        sheet.write(again_new_row,3,sum_feet_forty,cell_format)
        sheet.write(again_new_row,4,sum_feet_twenty,cell_format)
       
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
 
        return response