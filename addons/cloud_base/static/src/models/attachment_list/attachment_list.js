/** @odoo-module **/

import { registerInstancePatchModel } from "@mail/model/model_core";
import { replace } from "@mail/model/model_field_command";

registerInstancePatchModel("mail.attachment_list", "cloud_base/static/src/models/attachment_card/attachment_list.js", {
    /**
     * Re-write to consider synced attachments as not images
     */
    _computeImageAttachments() {
        return replace(this.attachments.filter(attachment => attachment.isImage && !attachment.cloudSynced));
    },

    /**
     * Re-write to consider synced images as cards
     */
    _computeNonImageAttachments() {
        return replace(this.attachments.filter(attachment => !attachment.isImage || attachment.cloudSynced));
    },
});
