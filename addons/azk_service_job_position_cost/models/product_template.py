from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = "product.template"
    
    use_designation_cost = fields.Boolean(string="Use Designation Cost", default=False)
    designation_cost_base = fields.Many2many('hr.job', string="Cost Based On Designation")
    designation_cost = fields.Float(string="Designation Cost", compute="_compute_designation_cost")
 
    def _compute_designation_cost(self):
        for rec in self:
            rec.designation_cost = 0
            designation_cost_calculate = self.env.company.designation_cost_calculate
            if rec.use_designation_cost and rec.designation_cost_base and designation_cost_calculate:
                list_of_time_costs = []
                employees_timesheet_cost = []
                time_cost = 0
                for emp  in rec.designation_cost_base.employee_ids.filtered(lambda a: a.active == True and a.contract_id.state == 'open'):
                    if emp.timesheet_cost:
                        list_of_time_costs.append(emp.timesheet_cost)
                employees_timesheet_cost = list_of_time_costs
                if employees_timesheet_cost:
                    if designation_cost_calculate == "lowest":
                        time_cost = min(employees_timesheet_cost)
                    elif designation_cost_calculate == "highest":
                        time_cost = max(employees_timesheet_cost)
                    elif designation_cost_calculate == "average":
                        if len(employees_timesheet_cost)> 0:
                            time_cost = sum(employees_timesheet_cost) / len(employees_timesheet_cost)
                    
                    rec.designation_cost = time_cost
                    