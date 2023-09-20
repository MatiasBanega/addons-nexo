from odoo import models


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["documents.mixin","account.move"]
    
    def write(self, vals):
        res = super().write(vals)
        if self and vals.get('state'):
            # when changing state the name of the entry will ne changes (from draft to name or from its name to Draft + name)
            # so on change of the state search for documents for this entry and change its name (couldn't be triggered by name
            # since name is a readonly field)
            document_workspaces = self.env["documents.folder"].sudo().search([('journal_entry_id', '=', self.id)])
            for doc in document_workspaces:
                doc.name = self.name
        return res
    
    def _get_document_folder(self):
        result = super()._get_document_folder()
        if self.company_id.use_specific_structure:
            account_docs_structure = self.company_id.account_documents_structure
            
            accounting_parent_workspace = self.company_id.account_folder
            if not account_docs_structure:
                result = accounting_parent_workspace
            
            elif account_docs_structure == 'by_entry':
                """ Folder for each Journal Entry in the Parent Account Folder """
                
                journal_entry_folder = self.env["documents.folder"].search([('journal_entry_id','=', self.id), ('parent_folder_id', '=', accounting_parent_workspace.id)], limit=1)
                if not journal_entry_folder:
                    journal_entry_folder = self.env["documents.folder"].create({'name' : self.name,
                                                                       'journal_entry_id' : self.id,
                                                                       'parent_folder_id' : accounting_parent_workspace.id
                                                                      })
                result = journal_entry_folder
            
            elif account_docs_structure == 'by_journal_entry':
                """ Folder for evry Journal in the Parent Account Folder and
                    every Journal Folder has Folders for every Journal Entry """
                
                journal_folder = self.env["documents.folder"].search([('journal_id','=', self.journal_id.id), ('parent_folder_id','=', accounting_parent_workspace.id)], limit=1)
                if not journal_folder:
                    journal_folder = self.env["documents.folder"].create({'name' : self.journal_id.name,
                                                                          'journal_id' : self.journal_id.id,
                                                                          'parent_folder_id' : accounting_parent_workspace.id
                                                                        })
                
                journal_entry_folder = self.env["documents.folder"].search([('journal_entry_id','=', self.id), ('parent_folder_id', '=', journal_folder.id)])
                if not journal_entry_folder:
                    journal_entry_folder = self.env["documents.folder"].create({'name' : self.name,
                                                                               'journal_entry_id' : self.id,
                                                                               'parent_folder_id' : journal_folder.id
                                                                              })
                result = journal_entry_folder
        return result