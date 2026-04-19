# ServiCentral Odoo Argentina

Repositorio base de localizacion argentina usado por ServiCentral sobre Odoo 18
Community.

Este repositorio no sigue el ritmo de releases del producto Field Service. Su
objetivo es mantenerse estable, con cambios puntuales y bien controlados para
facturacion, AFIP/ARCA, pagos, percepciones, retenciones y soporte contable
argentino.

## Estado actual

- Rama principal ServiCentral: `main`
- Base tecnica activa: `18.0`
- Snapshot estable actual: `servicentral-argentina-2026-04-19`

Las ramas historicas `13.0`, `15.0`, `16.0`, `17.0` y `18.0` pueden existir como
referencia tecnica o upstream. No representan versiones del producto
ServiCentral.

## Metodologia de ramas

Este repo usa una metodologia simple:

- `main`: estado estable consumido por ServiCentral.
- `18.0`: base tecnica Odoo/OCA o historica de migracion.
- `hotfix/nombre-corto`: correcciones puntuales.
- Tags fechados: snapshots estables usados por ServiCentral.

No se usan ramas `release/1.7`, `release/1.8` ni versiones del producto
ServiCentral en este repo. Esas versiones pertenecen al repositorio principal de
Field Service.

## Tags

Formato:

```text
servicentral-argentina-YYYY-MM-DD
```

Ejemplo:

```text
servicentral-argentina-2026-04-19
```

El tag marca una foto estable del repo que ServiCentral puede consumir o
desplegar junto con el stack principal.

## Flujo recomendado

Correccion puntual:

```text
main -> hotfix/nombre-corto -> main -> servicentral-argentina-YYYY-MM-DD
```

Cambios mas grandes deben dividirse en commits chicos y revisables. Si una rama
vieja contiene trabajo util, portarlo de forma acotada; no mergear ramas viejas
completas sin revisar el contexto.

## Reglas de desarrollo

- Mantener compatibilidad con Odoo 18 Community.
- No depender de Odoo Enterprise.
- Revisar manifests, dependencias, seguridad y datos XML antes de cerrar cambios.
- Cuidar compatibilidad con Python usado por el stack ServiCentral.
- Evitar cambios amplios si el problema requiere un hotfix puntual.
- Documentar cualquier criterio nuevo de localizacion o facturacion.
- Mantener ramas temporales cortas y borrarlas luego del merge.

## Areas funcionales

El repo incluye modulos para:

- factura electronica;
- AFIP/ARCA web services;
- cheques;
- recibos y pagos;
- percepciones;
- retenciones;
- Libro IVA Digital;
- reportes y mejoras UI de localizacion argentina.

## Desarrollo con IA

Cuando se use IA para asistir cambios en este repo:

- leer primero el modulo afectado y sus dependencias;
- no asumir que el comportamiento contable estandar de Odoo aplica sin revisar
  reglas argentinas;
- no revertir cambios manuales sin confirmacion;
- evitar refactors cosmeticos junto con fixes contables;
- dejar evidencia del diff y validaciones realizadas.

## Licencia

Este repositorio conserva las licencias de los modulos incluidos. Consultar cada
`__manifest__.py` para la licencia especifica de cada addon.
