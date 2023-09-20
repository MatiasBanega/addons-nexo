# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    "name": "Construction Management in Odoo",
    "version": "15.0.0.3",
    "depends": ['base', 'project', 'stock',
                'account', 'hr', 'purchase','sale','website_form_project','note','hr_timesheet',
                ],
    "author": "Browseinfo",
    "summary": "Construction Project management Building Construction Projects Construction cost center construction job order construction Cost Header construction Work Package construction Budgets Contractors job work order Real Estate  property  Bill of Quantity BOQ",
    "description": """
    BrowseInfo developed a new odoo/OpenERP module apps.
    This module use for Real Estate Management Construction management Building Construction,
    constuction projects Odoo construction management
    Odoo Construction Projects Construction system Odoo manage Construction
    cost center for construction system
    Odoo Construction apps
    construction job orders Construction work orders Odoo construction system
    This module allow you to create material purchase order directly from delivery.
    This module helps to manage Material planning  Consumed Materials of each job order(task) for construction project.
    construction Cost Code and construction Cost Header.
    construction Work Package
    construction Budgets
    construction Notes
    buidling construction management
    construction Materials
    construction Material Request For Job Orders
    Add Materials
    Job Orders
    Create Job Orders
    Job Order Related Notes
    Issues Related Project
    construction Vendors
    Vendors / construction Contractors constructor

    Construction Management
    Construction Activity
    Construction Jobs
    Job Order Construction
    Job Orders Issues
    Job Order Notes
    Construction Notes
    Job Order Reports
    Construction Reports
    Job Order Note
    Construction app
    Project Report
    Task Report
    Construction Project - Project Manager
    real estate property
    propery management
    Construction agency
    Construction Management
    bill of material
    Material Planning On Job Order

    Bill of Quantity On Job Order
    Bill of Quantity construction
    """,
    "website": "https://www.browseinfo.in",
    "data": [
        "security/ir.model.access.csv",
        'view/project.xml',
        "view/main_menu.xml",
        'view/bill_of_quantity_view.xml',
        'view/cost_code_view.xml',
        'view/cost_header_view.xml',
        'view/work_package_view.xml',
        'view/construction_management.xml',
        'report/construction_report.xml',
        'report/project_project_report.xml',
        'report/project_note_report.xml',
        'report/project_job_orders.xml',
        # Sub Task
        'view/sub_task.xml',
        
    ],
    "images": 'static/main_screenshot.png',
    "price": 49,
    "currency": 'EUR',
    'live_test_url': 'https://youtu.be/Jdhxf-UwQpY',
    "auto_install": False,
    "installable": True,
    "images": ['static/description/Banner.png'],
    "license": 'OPL-1',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
