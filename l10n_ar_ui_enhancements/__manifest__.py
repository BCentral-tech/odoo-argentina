{
    "name": "Argentina - UI Enhancements",
    "version": "18.0.1.0.0",
    "category": "Localization/Argentina",
    "summary": "Pequenos fixes de usabilidad para la localizacion argentina",
    "license": "AGPL-3",
    "author": "ServiCentral",
    "depends": [
        "account",
        "l10n_ar",
        "web",
    ],
    "data": [
        "views/res_partner_view.xml",
        "views/account_move_view.xml",
        "views/res_config_settings_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "l10n_ar_ui_enhancements/static/src/js/account_move_tax_warning.esm.js",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
