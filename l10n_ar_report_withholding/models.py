# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def btn_print_withholding(self):
        self.ensure_one()
        return self.env.ref(
            'l10n_ar_report_withholding.action_payment_withholdings'
        ).report_action(self)

    def _compute_print_withholding(self):
        for rec in self:
            rec.print_withholding = bool(rec.state == 'posted' and rec.tax_withholding_id)

    def _get_invoice_payment_amount(self, invoice):
        """Compatibility helper for the legacy withholding report on Odoo 18."""
        self.ensure_one()
        if not self.move_id or not invoice:
            return 0.0
        partials, _exchange_moves = self.move_id._get_reconciled_invoices_partials()
        amount = sum(
            abs(partial_amount)
            for _partial, partial_amount, counterpart_line in partials
            if counterpart_line.move_id == invoice
        )
        return invoice.currency_id.round(amount)

    def _get_receipt_withholding_lines(self):
        """Unified withholding lines for payment receipts on Odoo 18."""
        self.ensure_one()
        if 'l10n_ar_withholding_ids' in self._fields and self.l10n_ar_withholding_ids:
            return self.l10n_ar_withholding_ids
        return self.move_id.line_ids.filtered(
            lambda line: line.tax_line_id and (
                (
                    'l10n_ar_withholding_payment_type' in line.tax_line_id._fields
                    and line.tax_line_id.l10n_ar_withholding_payment_type in ('customer', 'supplier')
                )
                or (
                    'type_tax_use' in line.tax_line_id._fields
                    and line.tax_line_id.type_tax_use in ('customer', 'supplier')
                )
            )
        )

    print_withholding = fields.Boolean(
        'print_withholding',
        compute=_compute_print_withholding,
    )
