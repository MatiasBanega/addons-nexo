odoo.define('az_sale_brief.az_brief', function (require) {
    'use strict';

    require('web.dom_ready')

	initReplyButton();
	initSubmitButton();
	initConfirmButton();
	initAdjustButton();
	
	var ul_reply = false;
	
	function initReplyButton(){
		let $btn_reply = $(".btnReply")
		$btn_reply.click(function(e){
			let line_id =  this.getAttribute('data-brief_line_id');
			$('#brief_line_id').val(line_id);
			let self = $(e.target);
			/*let $div = $self.parent();
			let $ul = $($div.closest('ul'));*/
			ul_reply = self.parent().prev().prev();
			$("#azBriefModal").modal("show");
			$('#txtBriefReply').summernote();
		})
	}
	
	function initSubmitButton(){
		 $('#azSubmitBriefBtn').click(function(){
			let brief_line_id =  $('#brief_line_id').val();
			let reply_el =  $('#txtBriefReply');
			let reply =  reply_el.val();
			let color_id = '#question_color-' + brief_line_id;
			let bg_color = $(color_id).val();
			
			if(reply == ''){
				bootbox.alert('You must enter Reply.');
				return false;
			}
			
			$.ajax({
			    url: "/azk_sale_brief/add_reply",
				type: 'POST',
				async:false,
				data: {'brief_line_id': brief_line_id, 'reply': reply},
				beforeSend: function() {
		       		 $('#loader').removeClass('hidden')
		    	 },
				
				  }).done(function(data) {
					data = JSON.parse(data)
					if(data.status == 'error'){
						bootbox.alert(data.msg);
					}else{
						let li='';
						li ='<li class="list-group-item " style="background-color: '+ bg_color + '"><div class="row"><div class="col-sm-6 col-md-6 reply_info">';
						li += 'By: <span /> ' + data.partner + '</span></div><div class="col-sm-6 col-md-6 reply_info">';
						li += 'Date: <span  /> ' + Date.now() + '</span></div><hr />';
						li += '<div class="col-sm-12 col-md-12 reply_div">' + data.reply + '</div></div></li>'					
													
						ul_reply.prepend(li) ;

						reply_el.summernote('reset');
						$("#azBriefModal").modal("hide");
					}
					$('#loader').addClass('hidden');
					
				  }).fail(function() {
					bootbox.alert("unable to submit data");
					$('#loader').addClass('hidden');
			    
			  });
		});
	}
	
	function initConfirmButton(){
		$('#btnConfirmBrief').click(function(){
				let brief_id =  this.getAttribute('data-brief_id');
	
				$.ajax({
				    url: "/azk_sale_brief/confirm",
					type: 'POST',
					async:false,
					data: {'brief_id': brief_id},
					beforeSend: function() {
			       		 $('#loader').removeClass('hidden')
			    	 },
					
					  }).done(function(data) {
						data = JSON.parse(data)
						if(data.status == 'error'){
							bootbox.alert(data.msg);
						}else{
							location.reload()
						}
						
					  }).fail(function() {
						bootbox.alert("unable to submit data");
						$('#loader').addClass('hidden');
				    
				  });
			});
		}
		
	function initAdjustButton(){
		let $btnAdjustBrief = $('#btnAdjustBrief');
		$btnAdjustBrief.click(function(){
			let brief_id =  this.getAttribute('data-brief_id');
			
			$.ajax({
			    url: "/azk_sale_brief/ask_to_adjust",
				type: 'POST',
				async:false,
				data: {'brief_id': brief_id},
				beforeSend: function() {
		       		 $('#loader').removeClass('hidden')
		    	 },
				
				  }).done(function(data) {
					data = JSON.parse(data)
					if(data.status == 'error'){
						bootbox.alert(data.msg);
					}else{
						bootbox.alert('Your request has been submmited successfully.');
						location.reload();
					}
					$('#loader').addClass('hidden');
				  }).fail(function() {
					bootbox.alert("unable to submit data");
					$('#loader').addClass('hidden');
			    
			  });
		});
	}

})
