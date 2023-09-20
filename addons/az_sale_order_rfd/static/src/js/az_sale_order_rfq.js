odoo.define('az_sale_order_rfd.az_so_rfd', function (require) {
    'use strict';

    initRejectButton();
    initApproveButton();
    initSubmitRejectionButton();
    initPreviewFileBtn();
    
    
    function initRejectButton(){
        let $RejectBtn = $("#btnRejectRFD")
        
        $RejectBtn.click(function(e){
            let rfd_id =  this.getAttribute('data-rfd_id');
            $('#rfd_id').val(rfd_id);
            $("#azRFDReject").modal("show");
        })
    }
    
    function initSubmitRejectionButton(){
     $('#azSubmitRejectRFD').click(function(){
        
        let rfd_file_ids = {}
        $.each($(".rfd-comment"), function(idx, rfd_comment) {
            rfd_file_ids[rfd_comment.getAttribute('data-rfd_file_id')] = rfd_comment.value
        });
        
        if (rfd_file_ids != {}){
            $.ajax({
                url: "/sale_order_rfd/reject_rfd",
                type: 'POST',
                async: false,
                data: rfd_file_ids,
                
             }).done(function(data) {
                    data = JSON.parse(data)
                    if(data.status == 'error'){
                        alert(data.msg);
                    } else{
                        $("#azRFDReject").modal("hide");
                        location.reload();
                    }
                    
              }).fail(function() {
                   alert("Unable to submit data.");
                });
        }
      });
    }
    
    function initApproveButton(){
     $('#btnApproveRFD').click(function(){
        
        let rfd_id =  this.getAttribute('data-rfd_id');
        let survey_token = this.getAttribute('data-survey_token');
        $.ajax({
            url: "/sale_order_rfd/approve_rfd",
            type: 'POST',
            async: false,
            data: {'rfd_id': rfd_id},
            
         }).done(function(data) {
                data = JSON.parse(data)
                if(data.status == 'error'){
                    alert(data.msg);
                }
                else{
                    if (survey_token != undefined){
                        location.reload();
                        window.open(_.str.sprintf("/survey/start/%s?email=az_rfd_start_survey-%s", survey_token, rfd_id), '_blank');
                    }
                    else {
                        location.reload();
                    }
                }
                
          }).fail(function() {
               alert("Unable to submit data.");
            });
      });
    }
    
    function initPreviewFileBtn(){
        $('.PreviewRFDFile').click(function(){
            let rfd_file_id =  this.getAttribute('data-rfd_file_id');
            let rfd_file_access_token =  this.getAttribute('data-rfd_file_access_token');
            
            $("#preview_rfd_file_html").attr("src", _.str.sprintf("%s/web/content/%s?access_token=%s", window.origin, rfd_file_id, rfd_file_access_token))
            $("#azRFDPreviewFile").modal("show");
        });
        
        $("#closeRFDFilePreview").click(function() {
           $("#preview_rfd_file_html").attr("src", "")
        });
    }

});