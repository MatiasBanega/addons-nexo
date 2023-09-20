# -*- coding: utf-8 -*-
from odoo import models


class HrPayslipEmployees(models.TransientModel):
	_inherit = 'hr.payslip.employees'
	_description = 'Generate payslips for all selected employees'

	def _get_employees(self):
		"""
		Override to empty the employees which will be filled up by default on the creating batch payslip
		:return: False
		"""
		return False

	def _filter_contracts(self, contracts):
		"""
		Override this method to add the filter of structure when returning the contracts
		:param contracts: ['hr.contract'] recordset
		:return: filtered contracts
		"""
		contracts = super(HrPayslipEmployees, self)._filter_contracts(contracts)
		if self.structure_id:
			contracts = contracts.filtered(lambda x: x.structure_type_id.default_struct_id.id == self.structure_id.id)
		return contracts
