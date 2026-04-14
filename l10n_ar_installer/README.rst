Localizacion Argentina - Responsable Inscripto
==============================================

Meta modulo para instalar en un solo paso el paquete argentino que usamos de
forma recurrente para empresas responsables inscriptas.

Incluye:

* Localizacion contable argentina base
* Bancos argentinos
* AFIP Web Services
* Factura Electronica AFIP
* Padron AFIP / actualizacion de partners
* Datos extra de partners argentinos
* Recibos con multiples medios de pago
* Retenciones y reportes asociados
* Retenciones de pago Argentina precargadas
* Nombres de retenciones normalizados en espanol
* Libro IVA y Libro IVA Digital
* Impuestos por comprobante / move tax

Uso recomendado:

* instalar ``l10n_ar_installer`` en instancias de responsables inscriptos
  con ``l10n_ar_withholding`` disponible en el ``addons_path``
* instalar ``l10n_ar_installer_full`` si ademas se quiere FE, QR,
  percepciones y extras frecuentes
* instalar ``l10n_ar_installer_monotributista`` si se quiere un paquete
  reducido para monotributistas

No incluye a proposito:

* ``l10n_ar_stock`` y ``l10n_ar_report_stock`` porque requieren addons
  adicionales que no estan en este repositorio
* ``l10n_ar_rg5003`` porque depende de ``l10n_ar_report_fe`` y no esta en
  este repo
* ``l10n_ar_account_withholding_automatic`` porque es un carril funcional
  mas especifico y potencialmente superpuesto
