from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class AccountSimpleExpense(models.Model):
    _name = "account.simple.expense"
    _inherit = ["mail.thread.main.attachment", "mail.activity.mixin"]
    _description = "Gasto"
    _order = "date desc, id desc"
    _check_company_auto = True

    name = fields.Char(
        string="Numero",
        default=lambda self: _("Nuevo Gasto"),
        readonly=True,
        copy=False,
        tracking=True,
    )
    date = fields.Date(
        string="Fecha",
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Compania",
        required=True,
        default=lambda self: self.env.company,
        tracking=True,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Moneda",
        related="company_id.currency_id",
        readonly=True,
    )
    journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Diario de pago",
        required=True,
        check_company=True,
        domain="[('type', 'in', ['bank', 'cash', 'credit'])]",
        tracking=True,
    )
    account_id = fields.Many2one(
        comodel_name="account.account",
        string="Cuenta de gasto",
        required=True,
        check_company=True,
        domain="[('deprecated', '=', False), ('account_type', 'not in', ['asset_receivable', 'liability_payable', 'asset_cash', 'liability_credit_card', 'off_balance'])]",
        tracking=True,
    )
    tax_ids = fields.Many2many(
        comodel_name="account.tax",
        string="Impuestos",
        check_company=True,
        domain="[('type_tax_use', 'in', ['purchase', 'none'])]",
        tracking=True,
    )
    untaxed_amount = fields.Monetary(
        string="Base imponible",
        compute="_compute_tax_amounts",
        currency_field="currency_id",
        store=True,
    )
    tax_amount = fields.Monetary(
        string="Importe de impuestos",
        compute="_compute_tax_amounts",
        currency_field="currency_id",
        store=True,
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Contacto",
    )
    label = fields.Char(
        string="Descripcion",
        tracking=True,
    )
    amount = fields.Monetary(
        string="Total",
        required=True,
        currency_field="currency_id",
        tracking=True,
    )
    move_id = fields.Many2one(
        comodel_name="account.move",
        string="Asiento contable",
        readonly=True,
        copy=False,
        check_company=True,
    )
    reversal_move_id = fields.Many2one(
        comodel_name="account.move",
        string="Asiento de reversion",
        readonly=True,
        copy=False,
        check_company=True,
    )
    state = fields.Selection(
        selection=[
            ("draft", "Borrador"),
            ("posted", "Publicado"),
            ("cancelled", "Cancelado"),
        ],
        default="draft",
        required=True,
        copy=False,
    )

    @api.depends("amount", "company_id", "tax_ids")
    def _compute_tax_amounts(self):
        AccountTax = self.env["account.tax"]
        for expense in self:
            if not expense.tax_ids:
                expense.untaxed_amount = expense.amount
                expense.tax_amount = 0.0
                continue
            base_line = expense._prepare_tax_base_line()
            AccountTax._add_tax_details_in_base_line(base_line, expense.company_id)
            AccountTax._round_base_lines_tax_details([base_line], expense.company_id)
            tax_details = base_line["tax_details"]
            expense.untaxed_amount = tax_details["total_excluded_currency"]
            expense.tax_amount = (
                tax_details["total_included_currency"]
                - tax_details["total_excluded_currency"]
            )

    @api.constrains("amount")
    def _check_amount(self):
        for expense in self:
            if expense.amount <= 0:
                raise ValidationError(_("El importe debe ser mayor a cero."))

    @api.constrains("company_id", "journal_id", "account_id", "tax_ids")
    def _check_company_and_accounts(self):
        for expense in self:
            if expense.journal_id and expense.journal_id.company_id != expense.company_id:
                raise ValidationError(
                    _("El diario debe pertenecer a la compania del gasto.")
                )
            if expense.account_id and expense.company_id not in expense.account_id.company_ids:
                raise ValidationError(
                    _("La cuenta debe estar disponible para la compania del gasto.")
                )
            if any(tax.company_id != expense.company_id for tax in expense.tax_ids):
                raise ValidationError(
                    _("Los impuestos deben pertenecer a la compania del gasto.")
                )
            if (
                expense.journal_id.default_account_id
                and expense.account_id == expense.journal_id.default_account_id
            ):
                raise ValidationError(
                    _(
                        "La cuenta de gasto no puede ser la misma cuenta de liquidez del diario."
                    )
                )

    @api.onchange("company_id")
    def _onchange_company_id(self):
        for expense in self:
            if expense.journal_id.company_id != expense.company_id:
                expense.journal_id = False
            if expense.account_id and expense.company_id not in expense.account_id.company_ids:
                expense.account_id = False
            expense.tax_ids = expense.tax_ids.filtered(
                lambda tax: tax.company_id == expense.company_id
            )

    def action_post(self):
        for expense in self:
            if expense.state != "draft":
                continue
            liquidity_account = expense.journal_id.default_account_id
            if not liquidity_account:
                raise UserError(
                    _("El diario %s no tiene cuenta contable por defecto.")
                    % expense.journal_id.display_name
                )
            move = expense._create_account_move(liquidity_account)
            move.action_post()
            expense.write(
                {
                    "move_id": move.id,
                    "name": move.name,
                    "state": "posted",
                }
            )
        return True

    def _create_account_move(self, liquidity_account):
        self.ensure_one()
        line_name = self.label or _("Gasto")
        move_lines = self._prepare_move_lines(line_name, liquidity_account)
        return self.env["account.move"].create(
            {
                "move_type": "entry",
                "date": self.date,
                "journal_id": self.journal_id.id,
                "company_id": self.company_id.id,
                "ref": line_name,
                "line_ids": [Command.create(line) for line in move_lines],
            }
        )

    def _prepare_move_lines(self, line_name, liquidity_account):
        self.ensure_one()
        partner_id = self.partner_id.id or False
        if not self.tax_ids:
            return [
                {
                    "name": line_name,
                    "account_id": self.account_id.id,
                    "partner_id": partner_id,
                    "debit": self.amount,
                    "credit": 0.0,
                },
                {
                    "name": line_name,
                    "account_id": liquidity_account.id,
                    "partner_id": partner_id,
                    "debit": 0.0,
                    "credit": self.amount,
                },
            ]

        AccountTax = self.env["account.tax"]
        base_lines = [self._prepare_tax_base_line(partner_id=partner_id)]
        AccountTax._add_tax_details_in_base_lines(base_lines, self.company_id)
        AccountTax._round_base_lines_tax_details(base_lines, self.company_id)
        AccountTax._add_accounting_data_in_base_lines_tax_details(
            base_lines, self.company_id
        )
        tax_results = AccountTax._prepare_tax_lines(base_lines, self.company_id)

        move_lines = []
        for base_line, to_update in tax_results["base_lines_to_update"]:
            move_lines.append(
                {
                    "name": line_name,
                    "account_id": base_line["account_id"].id,
                    "partner_id": partner_id,
                    "tax_ids": [Command.set(base_line["tax_ids"].ids)],
                    "tax_tag_ids": to_update["tax_tag_ids"],
                    "amount_currency": to_update["amount_currency"],
                    "balance": to_update["balance"],
                    "currency_id": base_line["currency_id"].id,
                }
            )
        move_lines += tax_results["tax_lines_to_add"]
        move_lines.append(
            {
                "name": line_name,
                "account_id": liquidity_account.id,
                "partner_id": partner_id,
                "amount_currency": -self.amount,
                "balance": -self.amount,
                "currency_id": self.currency_id.id,
            }
        )
        return move_lines

    def _prepare_tax_base_line(self, partner_id=False):
        self.ensure_one()
        partner = self.env["res.partner"].browse(partner_id) if partner_id else self.partner_id
        return self.env["account.tax"]._prepare_base_line_for_taxes_computation(
            None,
            partner_id=partner,
            currency_id=self.currency_id,
            tax_ids=self.tax_ids,
            price_unit=self.amount,
            quantity=1.0,
            account_id=self.account_id,
            special_mode="total_included",
            sign=1.0,
        )

    def action_cancel(self):
        for expense in self:
            if expense.state == "draft":
                expense.state = "cancelled"
                continue
            if expense.state != "posted":
                continue
            reversal = expense.move_id._reverse_moves(
                default_values_list=[
                    {
                        "date": fields.Date.context_today(expense),
                        "ref": _("Reversion de %s") % expense.display_name,
                    }
                ],
                cancel=True,
            )
            expense.write(
                {
                    "reversal_move_id": reversal.id,
                    "state": "cancelled",
                }
            )
        return True

    def action_view_move(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Asiento contable"),
            "res_model": "account.move",
            "view_mode": "form",
            "res_id": self.move_id.id,
        }

    def unlink(self):
        posted_expenses = self.filtered(lambda expense: expense.state == "posted")
        if posted_expenses:
            raise UserError(_("No se pueden eliminar gastos publicados."))
        return super().unlink()
