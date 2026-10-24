# JA Video Studio — Guía de corrección de video LOG (Sony, Canon y DJI)

**Estado:** primera integración en fuente, en espera de CI Windows y de validación visual con metraje real (24 de octubre de 2026).

## Qué permite

En el inspector **Ajustar** de un clip de **video** aparece **Convertir LOG a Rec.709**. Selecciona el perfil grabado en tu cámara e importa su LUT de conversión técnica **3D `.cube`**. La aplicación no altera el video fuente: instala la LUT en la biblioteca local del usuario y la incluye como primer efecto del clip, antes de los ajustes de color creativos. Guardar, deshacer y editar los parámetros siguen el sistema nativo del proyecto.

Perfiles listados en esta entrega:
- Sony **S-Log3 / S-Gamut3.Cine**
- Sony **S-Log2 / S-Gamut**
- Canon **Log 2 / Cinema Gamut**
- Canon **Log 3 / Cinema Gamut**
- DJI **D-Log**
- DJI **D-Log M**, seleccionando la LUT oficial **específica del modelo** (Pocket, Action, Mini, Air, Mavic, etc.)

## Procedimiento previsto al pasar CI

1. Abre un proyecto SDR (Rec.709) e importa el video grabado en LOG.
2. Selecciona un solo clip de video desbloqueado en la línea de tiempo.
3. Abre el inspector **Ajustar**; en **Convertir LOG a Rec.709**, elige el perfil exacto (gamma y gamut).
4. Descarga la LUT técnica oficial correspondiente de Sony, Canon o DJI, descomprime el archivo descargado y selecciona el **`.cube` 3D** que transforma ese perfil a **Rec.709/BT.709**. Evita LUTs «creativas» y LUTs de otro modelo DJI.
5. Pulsa **Importar y aplicar LUT oficial (.cube)** y comprueba el antes/después del monitor.
6. Ajusta exposición, temperatura, contraste, ruedas y curvas desde el inspector original. **Quitar conversión LOG** elimina solo esa transformación. Deshacer permite recuperar el estado anterior.
7. Exporta una muestra corta y verifica tonos de piel, altas luces, negros y que la exportación coincide con la previsualización. Son pruebas manuales pendientes para esta entrega.

## Descargas oficiales de los fabricantes

- Sony: https://pro.sony/ls_MX/technology/professional-video-lut-look-up-table (perfiles de Sony con 3D LUT para S-Gamut/S-Log2 y S-Gamut.Cine/S-Log3).
- Canon: https://color.ssw.imaging-saas.canon/color/en/pc/import/ (Canon explica LUTs Log 2/3 a BT.709); descargas por cámara y Cine Gamut según modelo.
- DJI: https://www.dji.com/lut (elegir específicamente tu dispositivo: **D-Log** y **D-Log M** no son intercambiables).

**Importante:** por derechos de distribución y diferencias entre cámaras, JA Video Studio **no incluye archivos LUT oficiales de fabricante** en esta etapa. No interpreta de manera automática la gamma grabada ni garantiza que la LUT seleccionada coincida con el metraje. El usuario elige el perfil y la LUT; un archivo de otro gamut/rango o una LUT creativa puede dejar los colores incorrectos.

## Qué asegura el código y qué falta probar

- **Diseñado en fuente:** entradas de cámara diferenciadas de LUT creativas; identificador técnico estable por perfil y contenido; no sobrescribe una LUT anterior usada en otro proyecto; sustituye únicamente el transform de cámara activo en el clip; orden al inicio de la cadena de efectos; deshacer/rehacer mediante comandos existentes.
- **Pendiente de validar:** CI Rust y Slint, instalación Windows, comparación de captura LOG Sony/Canon/DJI, rangos de señal de cámara, calidad/consistencia de preview y exportación, proyectos exportados y reabiertos.
- **Limitación de portabilidad:** la LUT se instala en la carpeta local de Looks del usuario; el proyecto puede referenciarla, pero trasladarlo a otra PC **requiere instalar de nuevo** la LUT. La opción de empaquetar/revincular LUTs es trabajo posterior.
- **No incluido:** detección automática por metadata, conversión matemática integrada sin LUT, gestión de color ACES completa ni características móviles.

El desarrollo prioritario sigue siendo **JA Video Studio Windows**. **JA Connect / Android y la suite** continúan pospuestos hasta que la versión PC esté estable y funcional. Se conservan los 38 compromisos `EJ-001` … `EJ-038`, el inspector Texto original y PR #9 sin fusionar.
