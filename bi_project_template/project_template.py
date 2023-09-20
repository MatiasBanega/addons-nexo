from odoo import models, fields, api

class project_template_task(models.Model):

	_inherit = "project.task.type"

	project_check = fields.Boolean(string="Project Check")

class project_project(models.Model):

	_inherit = "project.project"

	# @api.model
	# def default_get(self, flds):
	# 	stage_type_obj = self.env['project.task.type']
	# 	state_new_id = stage_type_obj.search([('name', '=', 'New')], limit=1)
	# 	if state_new_id:
	# 		state_new_id.write({'sequence':1, 'project_check':True})
	# 	else:
	# 		state_new_id = stage_type_obj.create({'name':'New', 'sequence':1, 'project_check':True})
	# 	state_in_progress_id = stage_type_obj.search([('name', '=', 'In Progress')], limit=1)
	# 	if state_in_progress_id:
	# 		state_in_progress_id.write({'sequence':2, 'project_check':True})
	# 	else:
	# 		progress_id = stage_type_obj.create({'name':'In Progress', 'sequence':2, 'project_check':True})
	# 	state_cancel_id = stage_type_obj.search([('name', '=', 'Cancelled')], limit=1)
	# 	if state_cancel_id:
	# 		state_cancel_id.write({'sequence':3, 'project_check':True})
	# 	else:
	# 		cancel_id = stage_type_obj.create({'name':'Cancelled', 'sequence':3, 'project_check':True})
	# 	state_pending_id = stage_type_obj.search([('name', '=', 'Pending')], limit=1)
	# 	if state_pending_id:
	# 		state_pending_id.write({'sequence':4, 'project_check':True})
	# 	else:
	# 		pending_id = stage_type_obj.create({'name':'Pending', 'sequence':4, 'project_check':True})
	# 	state_closed_id = stage_type_obj.search([('name', '=', 'Closed')], limit=1)
	# 	if state_closed_id:
	# 		state_closed_id.write({'sequence':5, 'project_check':True})
	# 	else:
	# 		closed_id = stage_type_obj.create({'name':'Closed', 'sequence':4, 'project_check':True})
	# 	stage_list = []
	# 	result = super(project_project, self).default_get(flds)
	# 	for i in state_new_id:
	# 		result['stage_id'] = i.id
	# 	#result['task_count'] = True
	# 	return result

	def count_sequence(self):
		for a in self:
			stage_type_obj = a.env['project.task.type']
			state_in_progress_id = stage_type_obj.search([('name', '=', 'In Progress')], limit=1)
			state_template_id = stage_type_obj.search([('name', '=', 'Template')], limit=1)
			state_new_id = stage_type_obj.search([('name', '=', 'New')], limit=1)
			if a.stage_id.id == int(state_new_id):
				a.sequence_state = 1
			elif a.stage_id.id == int(state_in_progress_id):
				a.sequence_state = 2
			else:
				a.sequence_state = 3

	def set_template(self):
		for i in self:
			stage_type_obj = self.env['project.task.type']
			state_template_id = stage_type_obj.search([('name', '=', 'Template')], limit=1)
			state_new_id = stage_type_obj.search([('name', '=', 'New')], limit=1)
			if state_template_id:
				state_template_id.write({'sequence':1, 'project_check':True})
				state_new_id.update({'sequence':2, 'project_check':True})
				i.update({'stage_id':state_template_id.id, 'sequence_state':3})
			else:
				template_id = stage_type_obj.create({'name':'Template', 'sequence':1, 'project_check':True})
				template_id.write({'sequence':1, 'project_check':True})
				state_new_id.write({'sequence':2, 'project_check':True})
				i.write({'stage_id':template_id.id, 'sequence_state':3})
			state_template_id.write({'project_check':False})

	def new_project(self):
		for i in self:
			stage_type_obj = self.env['project.task.type']
			state_template_id = stage_type_obj.search([('name', '=', 'Template')], limit=1)
			state_new_id = stage_type_obj.search([('name', '=', 'New')], limit=1)
			test = i.name
			project_id = i.copy()
			if state_template_id:
				project_id.write({'stage_id':state_new_id.id, 'sequence_state':1})
				return project_id

	def reset_project(self):
		for i in self:
			stage_type_obj = self.env['project.task.type']
			state_new_id = stage_type_obj.search([('name', '=', 'New')], limit=1)
			if state_new_id:
				i.write({'stage_id':state_new_id.id, 'sequence_state':1})
			return 

	def set_progress(self):
		for i in self:
			stage_type_obj = self.env['project.task.type']
			state_progress_id = stage_type_obj.search([('name', '=', 'In Progress')], limit=1)
			if state_progress_id:
				i.write({'stage_id':state_progress_id.id, 'sequence_state':2})
			return 
			
	stage_id = fields.Many2one('project.project.stage', string="state")
	sequence_state = fields.Integer(compute="count_sequence", string="State Check")
