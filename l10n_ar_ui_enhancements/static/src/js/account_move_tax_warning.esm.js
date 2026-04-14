/** @odoo-module **/

import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { Many2ManyTagsField } from "@web/views/fields/many2many_tags/many2many_tags_field";

function shouldConfirmTaxEdition(component) {
    return (
        component.props.name === "tax_ids" &&
        component.props.record?.resModel === "account.move.line" &&
        component.relation === "account.tax"
    );
}

patch(Many2ManyTagsField.prototype, {
    setup() {
        super.setup(...arguments);
        this.dialogService = useService("dialog");
    },

    async update(recordlist) {
        if (!shouldConfirmTaxEdition(this) || !recordlist?.length) {
            return super.update(...arguments);
        }

        const confirmed = await this._confirmL10nArTaxEdition();
        if (!confirmed) {
            return;
        }
        return super.update(...arguments);
    },

    async deleteTag(id) {
        if (!shouldConfirmTaxEdition(this) || !id) {
            return super.deleteTag(...arguments);
        }

        const confirmed = await this._confirmL10nArTaxEdition();
        if (!confirmed) {
            return;
        }
        return super.deleteTag(...arguments);
    },

    async _confirmL10nArTaxEdition() {
        return new Promise((resolve) => {
            this.dialogService.add(
                ConfirmationDialog,
                {
                    title: _t("Modificar impuestos de la linea"),
                    body: _t(
                        "No se recomienda modificar manualmente los impuestos calculados por el sistema. Desea continuar?"
                    ),
                    confirmLabel: _t("Aceptar"),
                    cancelLabel: _t("Cancelar"),
                    confirmClass: "btn-danger",
                    confirm: () => resolve(true),
                    cancel: () => resolve(false),
                },
                {
                    onClose: () => resolve(false),
                }
            );
        });
    },
});
