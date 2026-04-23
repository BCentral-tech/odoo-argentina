from odoo import Command, fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestAccountSimpleExpense(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.cash_account = cls.env["account.account"].create(
            {
                "name": "Test Cash Simple Expense",
                "code": "TSE100",
                "account_type": "asset_cash",
                "company_ids": [Command.set(cls.company.ids)],
            }
        )
        cls.expense_account = cls.env["account.account"].create(
            {
                "name": "Test Expense Simple Expense",
                "code": "TSE500",
                "account_type": "expense",
                "company_ids": [Command.set(cls.company.ids)],
            }
        )
        cls.tax_account = cls.env["account.account"].create(
            {
                "name": "Test Tax Simple Expense",
                "code": "TSE210",
                "account_type": "asset_current",
                "company_ids": [Command.set(cls.company.ids)],
            }
        )
        cls.cash_journal = cls.env["account.journal"].create(
            {
                "name": "Test Cash Simple Expense",
                "code": "TSEJ",
                "type": "cash",
                "company_id": cls.company.id,
                "default_account_id": cls.cash_account.id,
            }
        )
        cls.purchase_tax = cls.env["account.tax"].create(
            {
                "name": "IVA Compra 21 Simple Expense",
                "amount_type": "percent",
                "amount": 21.0,
                "type_tax_use": "purchase",
                "company_id": cls.company.id,
            }
        )
        cls.purchase_tax.invoice_repartition_line_ids.filtered(
            lambda line: line.repartition_type == "tax"
        ).account_id = cls.tax_account
    def _create_expense(self, **kwargs):
        values = {
            "date": fields.Date.from_string("2026-04-19"),
            "company_id": self.company.id,
            "journal_id": self.cash_journal.id,
            "account_id": self.expense_account.id,
            "label": "Peaje ruta",
            "amount": 1200.0,
        }
        values.update(kwargs)
        return self.env["account.simple.expense"].create(values)

    def test_post_expense_creates_posted_journal_entry(self):
        expense = self._create_expense()

        expense.action_post()

        self.assertEqual(expense.state, "posted")
        self.assertEqual(expense.move_id.state, "posted")
        self.assertEqual(expense.name, expense.move_id.name)
        self.assertEqual(expense.move_id.journal_id, self.cash_journal)
        self.assertEqual(expense.move_id.date, fields.Date.from_string("2026-04-19"))

        expense_line = expense.move_id.line_ids.filtered(
            lambda line: line.account_id == self.expense_account
        )
        liquidity_line = expense.move_id.line_ids.filtered(
            lambda line: line.account_id == self.cash_account
        )
        self.assertEqual(len(expense_line), 1)
        self.assertEqual(len(liquidity_line), 1)
        self.assertRecordValues(
            expense_line,
            [{"debit": 1200.0, "credit": 0.0, "name": "Peaje ruta"}],
        )
        self.assertRecordValues(
            liquidity_line,
            [{"debit": 0.0, "credit": 1200.0, "name": "Peaje ruta"}],
        )

    def test_amount_must_be_positive(self):
        with self.assertRaises(ValidationError):
            self._create_expense(amount=0.0)

    def test_description_is_optional(self):
        expense = self._create_expense(label=False)

        expense.action_post()

        expense_line = expense.move_id.line_ids.filtered(
            lambda line: line.account_id == self.expense_account
        )
        self.assertEqual(expense.state, "posted")
        self.assertEqual(expense_line.name, "Gasto")

    def test_taxes_are_split_from_total_amount(self):
        expense = self._create_expense(
            amount=121.0,
            tax_ids=[Command.set(self.purchase_tax.ids)],
        )

        self.assertAlmostEqual(expense.untaxed_amount, 100.0)
        self.assertAlmostEqual(expense.tax_amount, 21.0)

        expense.action_post()

        base_line = expense.move_id.line_ids.filtered(
            lambda line: line.account_id == self.expense_account
        )
        tax_line = expense.move_id.line_ids.filtered(
            lambda line: line.account_id == self.tax_account
        )
        liquidity_line = expense.move_id.line_ids.filtered(
            lambda line: line.account_id == self.cash_account
        )
        self.assertEqual(len(base_line), 1)
        self.assertEqual(len(tax_line), 1)
        self.assertEqual(len(liquidity_line), 1)
        self.assertAlmostEqual(base_line.debit, 100.0)
        self.assertAlmostEqual(tax_line.debit, 21.0)
        self.assertAlmostEqual(liquidity_line.credit, 121.0)

    def test_journal_must_have_default_account_to_post(self):
        journal = self.cash_journal.copy(
            {
                "name": "Test Cash Without Account",
                "code": "TSEN",
                "default_account_id": False,
            }
        )
        expense = self._create_expense(journal_id=journal.id)

        with self.assertRaises(UserError):
            expense.action_post()

    def test_cancel_posted_expense_creates_reversal(self):
        expense = self._create_expense()
        expense.action_post()

        expense.action_cancel()

        reversal = self.env["account.move"].search(
            [("reversed_entry_id", "=", expense.move_id.id)]
        )
        self.assertEqual(expense.state, "cancelled")
        self.assertEqual(len(reversal), 1)
        self.assertEqual(reversal.state, "posted")
