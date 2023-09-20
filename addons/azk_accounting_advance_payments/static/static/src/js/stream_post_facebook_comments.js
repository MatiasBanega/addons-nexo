odoo.define('social.social_instagram_post_kanban_comments', function (require) {

var core = require('web.core');
var _t = core._t;

var FacebookComments = require('social.social_facebook_post_kanban_comments');

    FacebookComments.include({
        init: function (parent, options) {
            this._super.apply(this, arguments);
            if (this.options.originalPost.mediaType == 'instagram'){
                this.options.title = _t('Instagram Comments')
                this.originalPost.facebookAuthorId = false
             }
             this._super.apply(this, arguments);
        },
        
        getCommentLink: function (comment) {
            result = this._super.apply(this, arguments);
            if (comment.media_type == 'instagram') {
                result =  this.originalPost.postLink
            }
            return result
        },
        
        getAuthorPictureSrc: function (comment) {
            result = this._super.apply(this, arguments);
            if (!comment && this.originalPost && this.originalPost.mediaType && this.originalPost.mediaType == 'instagram') {
                result = this.originalPost.linkDescription
            }
            return result
        },
    
    });

});
