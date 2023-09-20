/** @odoo-module **/

import {
    registerInstancePatchModel,
    registerClassPatchModel,
    registerFieldPatchModel,
} from "@mail/model/model_core";
import { attr } from "@mail/model/model_field";


registerClassPatchModel("mail.attachment", "cloud_base/static/src/models/attachment/attachment.js", {
    /**
     * Re-write to pass data important for synced attachments
    */
    convertData(data) {
        const data2 = this._super(data);
        if ("cloud_key" in data && data.cloud_key) {
            data2.cloudSynced = true;
        }; 
        if ("mimetype" in data) {
            if (data.mimetype != "application/octet-stream") {
                data2.cloudDownloadable = true;
            };
        };
        if ("url" in data) {
            if (data.url) {
                data2.cloudURL = data.url;
            };
        };
        return data2
    },
});

registerInstancePatchModel("mail.attachment", "cloud_base/static/src/models/attachment/attachment.js", {               
    /** 
     * Re-write to bind this to our click events
     * binding should be fixed within https://github.com/odoo/owl/issues/876
    */
    _created() {
        this._super();
        this.openCloudLink = this.openCloudLink.bind(this);
    },
    /**
     * The method to open cloud link
     */
    openCloudLink(ev) {
        ev.stopPropagation();
        const action = {
            type: "ir.actions.act_url",
            target: "new",
            url: this.cloudURL,
        };
        this.env.bus.trigger("do-action", {action,});
    },
});

registerFieldPatchModel("mail.attachment", "cloud_base/static/src/models/attachment/attachment.js", {
    cloudURL: attr({
        default: false,
    }),
    cloudSynced: attr({
        default: false,
    }),
    cloudDownloadable: attr({
        default: false,
    }),
    for_delete: attr({
        default: false,
    }),
    cloud_key: attr({
        default: false,
    })
});
