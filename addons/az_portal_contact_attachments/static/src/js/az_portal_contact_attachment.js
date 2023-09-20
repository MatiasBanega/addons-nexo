odoo.define('az_portal_contact_attachments.contact_attachment', function (require) {
    'use strict';

    var core = require('web.core');
	var QWeb = core.qweb;
	var rpc = require('web.rpc');
	var session = require('web.session');
	require('web.dom_ready')
	
	
	$('#btnUploadCompanyDocumentModal').click(function(){
		$('#attachment_file').val("");
		$('#attachment_description').val("");
		$("#contactUploadAttachmentModal").modal("show");
	})
	
	$('#upload_contact_file').click(function(){
			var $file = $('#attachment_file');
			var $desc = $('#attachment_description');
			
			if($file[0].files.length == 0){
				bootbox.alert("File is required");
				return false;
			}
			
			if($desc.val() == ""){
				bootbox.alert("Description is required");
				return false;
			}
			
			var formData = new FormData();
			if($file[0].files.length > 0){
				var att_file =  $file[0].files[0];
				formData.append('contact_file', att_file, att_file.name);
				formData.append('description', $desc.val());
				
				$.ajax({
					    url: "/company_documents/upload",
						type: 'POST',
						async:false, 
						data: formData,
						processData: false,
						contentType: false,
						xhr: function () {
								return new XMLHttpRequest();
							},
						beforeSend: function() {
				       		 $('#loader').removeClass('hidden')
				    	 },
					  }).done(function(data) {
						data = JSON.parse(data)
						if(data.status == 'fail'){
							bootbox.alert(data.msg);
							$('#loader').addClass('hidden');
						}						
						else
						 	location.reload();
					  }).fail(function() {
			    	 	bootbox.alert("Could not upload attachment");
						$('#loader').addClass('hidden');
				  	});
			}
				
		})
		
		$('#deleteCompanyDocument').click(function(){
			let attachemnt_id =  this.getAttribute('data-attachemnt_id');

			$.ajax({
			    url: "/company_documents/delete",
				type: 'POST',
				data: {attachment_id: attachemnt_id} ,
			  }).done(function(data) {
				data = JSON.parse(data)
				if(data.status == 'fail'){
					bootbox.alert(data.msg);
					$('#loader').addClass('hidden');
				}	
				else
				 	location.reload();
			  }).fail(function() {
			    bootbox.alert('Unable to delete documnet');
				$('#loader').addClass('hidden');
			});

		})
		
		
	
})
