/** @odoo-module */

import { _lt } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";


export class PdfOptionsModal extends Dialog {
    executePdfAction(option) {
        this.props.onSelectOption(option);
    }
    close() {
        this.props.onClose();
        super.close();
    }
}

PdfOptionsModal.size = "model-sm";
PdfOptionsModal.title = _lt("What do you want to do?");
PdfOptionsModal.bodyTemplate = "report_pdf_options.ButtonOptions";
