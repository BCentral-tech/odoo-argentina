from odoo import _, api, fields, models
from odoo.exceptions import UserError


CONSUMER_FINAL_IDENTIFICATION_PARAM = (
    "l10n_ar_ui_enhancements.consumer_final_identification_amount"
)
CONSUMER_FINAL_IDENTIFICATION_DEFAULT = 10000000.0


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_ar_partner_config_warning = fields.Char(
        string="Advertencia configuracion fiscal",
        compute="_compute_l10n_ar_partner_config_warning",
    )

    @api.depends(
        "partner_id",
        "partner_id.commercial_partner_id",
        "partner_id.commercial_partner_id.l10n_ar_afip_responsibility_type_id",
        "partner_id.commercial_partner_id.l10n_latam_identification_type_id",
        "partner_id.commercial_partner_id.vat",
        "company_id.account_fiscal_country_id",
        "journal_id.l10n_latam_use_documents",
        "amount_total",
        "move_type",
        "state",
    )
    def _compute_l10n_ar_partner_config_warning(self):
        for move in self:
            move.l10n_ar_partner_config_warning = False
            issues = move._l10n_ar_get_partner_config_issues()
            if not issues:
                continue

            if len(issues) == 1:
                issues_text = issues[0]
            else:
                issues_text = _("%s y %s") % (issues[0], issues[1])

            move.l10n_ar_partner_config_warning = _(
                'Complete o corrija %s del cliente "%s".\nDespues de guardar el cliente, vuelva a la factura para continuar.'
            ) % (issues_text, move.partner_id.commercial_partner_id.display_name)

    @api.model
    def _l10n_ar_get_consumer_final_identification_amount(self):
        param_value = (
            self.env["ir.config_parameter"].sudo().get_param(
                CONSUMER_FINAL_IDENTIFICATION_PARAM
            )
            or CONSUMER_FINAL_IDENTIFICATION_DEFAULT
        )
        try:
            return float(param_value)
        except (TypeError, ValueError):
            return CONSUMER_FINAL_IDENTIFICATION_DEFAULT

    def _l10n_ar_is_customer_document_for_partner_checks(self):
        self.ensure_one()
        return bool(
            self.company_id.account_fiscal_country_id.code == "AR"
            and self.l10n_latam_use_documents
            and self.is_sale_document(include_receipts=True)
            and self.partner_id
        )

    def _l10n_ar_is_consumer_final_identification_required(self):
        self.ensure_one()
        if not self._l10n_ar_is_customer_document_for_partner_checks():
            return False

        partner = self.partner_id.commercial_partner_id
        if partner.l10n_ar_afip_responsibility_type_id.code != "5":
            return True

        threshold = self._l10n_ar_get_consumer_final_identification_amount()
        return abs(self.amount_total) >= threshold

    def _l10n_ar_prepare_consumer_final_partner(self):
        sigd_identification_type = self.env.ref("l10n_ar.it_Sigd", raise_if_not_found=False)
        if not sigd_identification_type:
            return

        for move in self:
            if not move._l10n_ar_is_customer_document_for_partner_checks():
                continue

            partner = move.partner_id.commercial_partner_id
            if (
                partner.l10n_ar_afip_responsibility_type_id.code == "5"
                and not move._l10n_ar_is_consumer_final_identification_required()
                and not partner.l10n_latam_identification_type_id
                and not partner.vat
            ):
                partner.l10n_latam_identification_type_id = sigd_identification_type

    def _l10n_ar_get_partner_config_issues(self):
        self.ensure_one()
        if not self._l10n_ar_is_customer_document_for_partner_checks():
            return []

        partner = self.partner_id.commercial_partner_id
        issues = []
        if not partner.l10n_ar_afip_responsibility_type_id:
            issues.append(_("la Responsabilidad ARCA"))

        identification_type = partner.l10n_latam_identification_type_id
        identification_code = identification_type.l10n_ar_afip_code
        has_identification = bool(identification_type and partner.vat)
        has_partial_identification = bool(identification_type) != bool(partner.vat)
        requires_identification = self._l10n_ar_is_consumer_final_identification_required()

        if requires_identification and not has_identification:
            issues.append(_("la identificacion fiscal (CUIT/DNI)"))
        elif not requires_identification and has_partial_identification and identification_code != "99":
            issues.append(_("la identificacion fiscal completa o usar Sin Identificar (SIGD)"))
        elif has_identification and partner._l10n_ar_has_hyphenated_cuit():
            issues.append(_("el CUIT sin guiones"))
        return issues

    @api.onchange("partner_id")
    def _onchange_afip_responsibility(self):
        self.ensure_one()
        if self._l10n_ar_is_customer_document_for_partner_checks() and not self.partner_id.commercial_partner_id.l10n_ar_afip_responsibility_type_id:
            return
        return super()._onchange_afip_responsibility()

    @api.depends(
        "journal_id",
        "partner_id",
        "partner_id.commercial_partner_id",
        "partner_id.commercial_partner_id.l10n_ar_afip_responsibility_type_id",
        "company_id",
        "move_type",
        "debit_origin_id",
    )
    def _compute_l10n_latam_available_document_types(self):
        return super()._compute_l10n_latam_available_document_types()

    @api.depends(
        "l10n_latam_available_document_type_ids",
        "partner_id.commercial_partner_id.l10n_ar_afip_responsibility_type_id",
    )
    def _compute_l10n_latam_document_type(self):
        return super()._compute_l10n_latam_document_type()

    @api.onchange("partner_id", "journal_id")
    def _onchange_l10n_ar_refresh_document_type(self):
        self.ensure_one()
        if not (self.state == "draft" and self.journal_id and self._l10n_ar_is_customer_document_for_partner_checks()):
            return

        self._compute_l10n_latam_available_document_types()
        document_types = self.l10n_latam_available_document_type_ids._origin
        if self.debit_origin_id:
            document_types = document_types.filtered(lambda doc: doc.internal_type == "debit_note")

        self.l10n_latam_document_type_id = document_types[:1].id if document_types else False
        self._onchange_l10n_latam_document_type_id()

    def _post(self, soft=True):
        for move in self.filtered(
            lambda m: m.company_id.account_fiscal_country_id.code == "AR"
            and m.l10n_latam_use_documents
            and m.is_sale_document(include_receipts=True)
            and m.partner_id
        ):
            move._l10n_ar_prepare_consumer_final_partner()
            issues = move._l10n_ar_get_partner_config_issues()
            if not issues:
                continue
            if len(issues) == 1:
                issues_text = issues[0]
            else:
                issues_text = _("%s y %s") % (issues[0], issues[1])
            raise UserError(
                _(
                    'No puede continuar con la factura de "%s" hasta corregir %s en el contacto.'
                )
                % (move.partner_id.commercial_partner_id.display_name, issues_text)
            )
        return super()._post(soft=soft)

    def action_open_partner_for_completion(self):
        self.ensure_one()
        partner = self.partner_id.commercial_partner_id
        if not partner:
            return False
        return {
            "type": "ir.actions.act_window",
            "name": _("Cliente"),
            "res_model": "res.partner",
            "view_mode": "form",
            "res_id": partner.id,
            "target": "current",
            "context": {
                "form_view_initial_mode": "edit",
            },
        }
