from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    l10n_ar_consumer_final_identification_amount = fields.Float(
        string="Monto para exigir identificacion a consumidor final",
        config_parameter="l10n_ar_ui_enhancements.consumer_final_identification_amount",
        default=10000000.0,
        help=(
            "Si la factura de cliente a consumidor final alcanza este monto, se exige "
            "identificacion fiscal. Por debajo de ese valor se permite Sin Identificar "
            "(SIGD). Use 0 para exigir identificacion siempre."
        ),
    )
