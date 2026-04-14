from odoo import _, api, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _l10n_ar_has_hyphenated_cuit(self):
        self.ensure_one()
        partner = self.commercial_partner_id
        return (
            partner.l10n_latam_identification_type_id.l10n_ar_afip_code == "80"
            and bool(partner.vat)
            and "-" in partner.vat
        )

    @api.constrains("vat", "l10n_latam_identification_type_id")
    def _check_l10n_ar_cuit_without_hyphen(self):
        for partner in self:
            if partner.commercial_partner_id._l10n_ar_has_hyphenated_cuit():
                raise ValidationError(_("El CUIT debe cargarse sin guiones."))

    @api.onchange("vat", "l10n_latam_identification_type_id")
    def _onchange_l10n_ar_cuit_without_hyphen(self):
        if self.commercial_partner_id._l10n_ar_has_hyphenated_cuit():
            return {
                "warning": {
                    "title": _("CUIT invalido"),
                    "message": _("El CUIT debe cargarse sin guiones."),
                }
            }
