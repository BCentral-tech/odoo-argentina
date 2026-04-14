from odoo.addons.l10n_ar.tests.common import TestArCommon


class TestL10nArUiEnhancements(TestArCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.config_parameter"].sudo().set_param(
            "l10n_ar_ui_enhancements.consumer_final_identification_amount",
            1000,
        )

    def _new_move_for_checks(self, move_type, partner):
        journal_type = "sale" if move_type.startswith("out_") else "purchase"
        journal = self.env["account.journal"].search(
            [
                ("company_id", "=", self.company_ri.id),
                ("type", "=", journal_type),
                ("l10n_latam_use_documents", "=", True),
            ],
            limit=1,
        )
        return self.env["account.move"].new(
            {
                "move_type": move_type,
                "partner_id": partner.id,
                "company_id": self.company_ri.id,
                "journal_id": journal.id,
                "l10n_latam_use_documents": True,
                "state": "draft",
            }
        )

    def test_vendor_bill_is_not_blocked_by_customer_checks(self):
        vendor = self.env["res.partner"].create({"name": "Proveedor sin datos fiscales"})

        bill = self._new_move_for_checks("in_invoice", vendor)

        self.assertEqual(bill._l10n_ar_get_partner_config_issues(), [])

    def test_customer_invoice_still_requires_partner_tax_data(self):
        customer = self.env["res.partner"].create({"name": "Cliente sin datos fiscales"})

        invoice = self._new_move_for_checks("out_invoice", customer)
        issues = invoice._l10n_ar_get_partner_config_issues()

        self.assertTrue(any("Responsabilidad" in issue for issue in issues))
        self.assertTrue(any("identificacion fiscal" in issue for issue in issues))

    def test_consumer_final_below_threshold_allows_anonymous_partner_and_sets_sigd(self):
        consumer_final = self.env["res.partner"].create(
            {
                "name": "Consumidor final ocasional",
                "l10n_ar_afip_responsibility_type_id": self.env.ref("l10n_ar.res_CF").id,
            }
        )
        invoice = self._create_invoice_ar(
            partner_id=consumer_final,
            company_id=self.company_ri,
            invoice_line_ids=[
                self._prepare_invoice_line(price_unit=500, product_id=self.product_iva_21)
            ],
        )

        self.assertEqual(invoice._l10n_ar_get_partner_config_issues(), [])

        self._post(invoice)
        self.assertEqual(
            consumer_final.l10n_latam_identification_type_id,
            self.env.ref("l10n_ar.it_Sigd"),
        )

    def test_consumer_final_above_threshold_requires_identification(self):
        consumer_final = self.env["res.partner"].create(
            {
                "name": "Consumidor final identificado",
                "l10n_ar_afip_responsibility_type_id": self.env.ref("l10n_ar.res_CF").id,
            }
        )
        invoice = self._create_invoice_ar(
            partner_id=consumer_final,
            company_id=self.company_ri,
            invoice_line_ids=[
                self._prepare_invoice_line(price_unit=1500, product_id=self.product_iva_21)
            ],
        )

        issues = invoice._l10n_ar_get_partner_config_issues()
        self.assertTrue(any("identificacion fiscal" in issue for issue in issues))
