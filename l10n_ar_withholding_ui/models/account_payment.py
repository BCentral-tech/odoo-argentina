from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    l10n_ar_related_move_ids = fields.Many2many(
        "account.move",
        string="Comprobantes involucrados",
        compute="_compute_l10n_ar_related_move_ids",
    )
    l10n_ar_withholding_base_total = fields.Monetary(
        string="Subtotal base",
        currency_field="currency_id",
        compute="_compute_l10n_ar_withholding_totals",
    )
    l10n_ar_withholding_amount_total = fields.Monetary(
        string="Subtotal retenido",
        currency_field="currency_id",
        compute="_compute_l10n_ar_withholding_totals",
    )

    @api.depends("reconciled_invoice_ids", "reconciled_bill_ids")
    def _compute_l10n_ar_related_move_ids(self):
        for rec in self:
            rec.l10n_ar_related_move_ids = rec.reconciled_invoice_ids | rec.reconciled_bill_ids

    @api.depends("l10n_ar_withholding_ids.tax_base_amount", "l10n_ar_withholding_ids.amount_currency")
    def _compute_l10n_ar_withholding_totals(self):
        for rec in self:
            unique_bases = {abs(line.tax_base_amount) for line in rec.l10n_ar_withholding_ids}
            rec.l10n_ar_withholding_base_total = sum(unique_bases)
            rec.l10n_ar_withholding_amount_total = sum(abs(line.amount_currency) for line in rec.l10n_ar_withholding_ids)
