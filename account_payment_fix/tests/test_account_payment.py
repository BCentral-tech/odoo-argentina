from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestAccountPaymentFix(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.payment_model = cls.env["account.payment"]

    def _new_payment(self, payment_type="inbound"):
        return self.payment_model.new(
            {
                "payment_type": payment_type,
                "partner_type": "customer",
                "company_id": self.env.company.id,
            }
        )

    def test_onchange_payment_type_without_payment_group_invoice_lines(self):
        payment = self._new_payment("outbound")

        payment._onchange_payment_type()

        self.assertEqual(payment.partner_type, "supplier")

    def test_compute_destination_account_without_payment_group_transfer_field(self):
        payment = self._new_payment()

        payment._compute_destination_account_id()

        self.assertIn("destination_account_id", payment._fields)
