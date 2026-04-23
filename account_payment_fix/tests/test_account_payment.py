from odoo import Command
from odoo.tests.common import TransactionCase


class TestAccountPaymentFix(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.cash_account = cls.env["account.account"].create(
            {
                "name": "Test Cash Payment Fix",
                "code": "TPF100",
                "account_type": "asset_cash",
                "company_ids": [Command.set(cls.company.ids)],
            }
        )
        cls.cash_journal = cls.env["account.journal"].create(
            {
                "name": "Test Cash Payment Fix",
                "code": "TPFJ",
                "type": "cash",
                "company_id": cls.company.id,
                "default_account_id": cls.cash_account.id,
            }
        )

    def test_onchange_payment_type_without_invoice_line_ids_uses_odoo18_fields(self):
        payment = self.env["account.payment"].new(
            {
                "payment_type": "inbound",
                "partner_type": "supplier",
                "journal_id": self.cash_journal.id,
            }
        )

        payment._onchange_payment_type()

        self.assertEqual(payment.partner_type, "customer")
        self.assertFalse(payment.journal_id)
