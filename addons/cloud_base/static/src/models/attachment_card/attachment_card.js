/** @odoo-module **/

import { registerInstancePatchModel } from "@mail/model/model_core";

registerInstancePatchModel("mail.attachment_card", "cloud_base/static/src/models/attachment_card/attachment_card.js", {
    /**
     * Re-write to open url if preview is not available
     */
    onClickImage(ev) {
        if ((!this.attachment || !this.attachment.isViewable) && this.attachment.cloudURL) {
            this.attachment.openCloudLink(ev);
            return
        }
        else {this._super(ev);}
    },
});
