from odoo import fields
from odoo.addons.l10n_ar.tests.common import TestArCommon


class TestAfipwsFeMove(TestArCommon):
    def _new_ar_move(self, document_type, **extra_vals):
        journal = self.env["account.journal"].search(
            [
                ("company_id", "=", self.company_ri.id),
                ("type", "=", "sale"),
                ("l10n_latam_use_documents", "=", True),
            ],
            limit=1,
        )
        vals = {
            "move_type": "out_invoice",
            "partner_id": self.res_partner_adhoc.id,
            "company_id": self.company_ri.id,
            "journal_id": journal.id,
            "invoice_date": fields.Date.to_date("2026-04-17"),
            "l10n_latam_document_type_id": document_type.id,
            "state": "posted",
        }
        vals.update(extra_vals)
        return self.env["account.move"].new(vals)

    def test_reversal_uses_reversed_entry_as_related_invoice(self):
        invoice = self._new_ar_move(
            self.document_type["invoice_a"],
            document_number="00004-00003105",
        )
        credit_note = self._new_ar_move(
            self.document_type["credit_note_a"],
            move_type="out_refund",
            invoice_origin="OS000258, OS000513",
            reversed_entry_id=invoice,
        )

        self.assertEqual(credit_note.get_related_invoices_data(), invoice)

    def test_debit_note_uses_debit_origin_as_related_invoice(self):
        invoice = self._new_ar_move(
            self.document_type["invoice_a"],
            document_number="00004-00003105",
        )
        debit_note = self._new_ar_move(
            self.env.ref("l10n_ar.dc_a_nd"),
            move_type="out_invoice",
            invoice_origin="OS000258, OS000513",
            debit_origin_id=invoice,
        )

        self.assertEqual(debit_note.get_related_invoices_data(), invoice)

    def test_associated_period_is_capped_to_invoice_date(self):
        credit_note = self._new_ar_move(
            self.document_type["credit_note_a"],
            move_type="out_refund",
            invoice_date=fields.Date.to_date("2026-04-17"),
            l10n_ar_afip_service_start=fields.Date.to_date("2026-04-01"),
            l10n_ar_afip_service_end=fields.Date.to_date("2026-04-30"),
        )

        self.assertEqual(
            credit_note._l10n_ar_get_associated_period_dates(),
            (
                fields.Date.to_date("2026-04-01"),
                fields.Date.to_date("2026-04-17"),
            ),
        )
