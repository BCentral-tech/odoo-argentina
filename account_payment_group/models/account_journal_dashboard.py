from odoo import models

class AccountJournal(models.Model):
    _inherit = "account.journal"

    def open_payments_action(self, payment_type, mode='form'):
        return super(AccountJournal, self).open_payments_action(payment_type,mode)
