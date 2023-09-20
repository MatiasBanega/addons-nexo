from odoo import models


class Project(models.Model):
    _inherit = 'project.project'
    
    def _get_document_folder(self):
        documents_folder_object = self.env["documents.folder"]
        
        res = super()._get_document_folder()
        
        project_documents_structure = self.company_id.project_documents_structure
        if project_documents_structure:
            if project_documents_structure in ['by_project', 'by_project_task']:
                project_folder_id = documents_folder_object.search([('project_id','=', self.id), ('parent_folder_id','=', self.company_id.project_folder.id)], limit=1)
                if project_folder_id:
                    res = project_folder_id
                else:
                    res = documents_folder_object.create({'name': self.name,
                                                          'project_id' : self.id,
                                                          'parent_folder_id' : self.company_id.project_folder.id
                                                        })
            
            elif project_documents_structure in ['by_customer_project', 'by_customer_project_task']:
                # checking if it belongs to a customer
                if self.partner_id:
                    customer_folder = documents_folder_object.search([('project_customer_id', '=' , self.partner_id.id), ('parent_folder_id','=', self.company_id.project_folder.id)], limit=1)
                    if not customer_folder:
                        customer_folder = documents_folder_object.create({'name' : self.partner_id.name,
                                                                          'project_customer_id' : self.partner_id.id,
                                                                          'parent_folder_id' : self.company_id.project_folder.id
                                                                          })
                    
                    project_folder_id = documents_folder_object.search([('parent_folder_id', '=', customer_folder.id), ('project_id', '=', self.id)], limit=1)
                    if not project_folder_id:
                        project_folder_id = documents_folder_object.create({'name': self.name,
                                                                            'project_id' : self.id,
                                                                            'parent_folder_id' : customer_folder.id
                                                                           })
                    res = project_folder_id
                    
        return res
    
    
class ProjectTask(models.Model):
    _inherit = 'project.task'
    
    def _get_document_folder(self):
        documents_folder_object = self.env["documents.folder"]
        res = super()._get_document_folder()
        
        project_documents_structure = self.company_id.project_documents_structure
        if project_documents_structure:
            if project_documents_structure == 'by_project':
                project_folder_id = documents_folder_object.search([('project_id','=', self.project_id.id), ('parent_folder_id','=', self.company_id.project_folder.id)], limit=1)
                if project_folder_id:
                    res = project_folder_id
                else:
                    res = documents_folder_object.create({'name': self.project_id.name,
                                                          'project_id' : self.project_id.id,
                                                          'parent_folder_id' : self.company_id.project_folder.id
                                                        })
            
            elif project_documents_structure == 'by_project_task':
                project_folder = documents_folder_object.search([('project_id','=', self.project_id.id), ('parent_folder_id','=', self.company_id.project_folder.id)], limit=1)
                
                if not project_folder:
                    project_folder = documents_folder_object.create({'name': self.project_id.name,
                                                                      'project_id' : self.project_id.id,
                                                                      'parent_folder_id' : self.company_id.project_folder.id
                                                                    })
                task_folder = documents_folder_object.search([('project_task_id', '=', self.id), ('parent_folder_id','=', project_folder.id)], limit=1)
                if not task_folder:
                    task_folder = documents_folder_object.create({'name' : self.name,
                                                                  'project_task_id' : self.id,
                                                                  'parent_folder_id' : project_folder.id,
                                                                  })
                res = task_folder
                
            elif project_documents_structure in ['by_customer_project', 'by_customer_project_task']:
                # checking if it belongs to a customer
                if self.partner_id:
                    customer_folder = documents_folder_object.search([('project_customer_id', '=' , self.partner_id.id), ('parent_folder_id','=', self.company_id.project_folder.id)], limit=1)
                    if not customer_folder:
                        customer_folder = documents_folder_object.create({'name' : self.partner_id.name,
                                                                          'project_customer_id' : self.partner_id.id,
                                                                          'parent_folder_id' : self.company_id.project_folder.id
                                                                          })
                    
                    project_folder_id = documents_folder_object.search([('parent_folder_id', '=', customer_folder.id), ('project_id', '=', self.project_id.id)], limit=1)
                    if not project_folder_id:
                        project_folder_id = documents_folder_object.create({'name': self.project_id.name,
                                                                            'project_id' : self.project_id.id,
                                                                            'parent_folder_id' : customer_folder.id
                                                                           })
                    if project_documents_structure == 'by_customer_project':
                        res = project_folder_id
                    
                    else: # by_customer_project_task
                        task_folder = documents_folder_object.search([('project_task_id', '=', self.id), ('parent_folder_id', '=', project_folder_id.id)], limit=1)
                        if not task_folder:
                            task_folder = documents_folder_object.create({'name' : self.name,
                                                                          'project_task_id' : self.id,
                                                                          'parent_folder_id' : project_folder_id.id,
                                                                          })
                        res = task_folder
                    
        return res