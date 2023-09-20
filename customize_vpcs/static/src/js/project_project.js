odoo.define('customize_vpcs.project_project', function (require) {
"use strict";

var core = require('web.core');
var FormController = require('web.FormController')

var _t = core._t;
var QWeb = core.qweb;

FormController.include({
	_onEdit: function () {
		if (this.modelName == "project.project"){
			if (this.renderer.state.data.edit_button_check_bool){
				this._super();
			}
			if (this.renderer.state.data.lock_document_check_bool){
				return;
			}
			if (this.renderer.state.data.state_completed_check_bool){
				return;
			}
			var currentId = this.getSelectedIds();
   			var d = new Date();
   			var month = d.getMonth()+1;
   			var day = d.getDate();
   			var output = d.getFullYear() + '-' +
		    ((''+month).length<2 ? '0' : '') + month + '-' +
		    ((''+day).length<2 ? '0' : '') + day; 
			if (this.renderer.state.data.end_date._i == output){
				return;
			}			
			else{
        		this._super();
			}
		}
		else{
			this._super();
		}
		
    },

})
});