# Estudio Joven — Ruta crítica de entregas

**Fecha de decisión:** 24 de octubre de 2026. La prioridad es una aplicación útil y comprobable, no la cantidad de funciones implementadas. Este plan coordina el registro maestro; no reemplaza sus 38 criterios.

## Orden de construcción y condiciones de paso

### Puerta A — Fase 3: estabilizar antes de extender

**BLOQUEO ACTUAL (CI #40112515736):** 171 pruebas Rust aprobadas pero build Windows falló al compilar `captions.slint` por punto y coma en lugar de coma en campos de `CaptionsSheetData` (líneas 61–68). Objetivo siguiente: verificar la rama actual, corregir sólo esas declaraciones en código fuente, ejecutar un workflow y resolver el siguiente error real si aparece. Véase `docs/CONTINUIDAD_CHATGPT.md`. Hasta pasar esa puerta, no avanzar a fases de karaoke/Glow/TTS.

- Verificar que el PR #9 compile Rust **y Slint**, pase pruebas, arranque y genere instalador. Si falla, arreglar esa misma rama antes de iniciar otra implementación.
- Probar manualmente en Windows: Whisper con voz en español; Generar / Editar; selección de frase; Aplicar, Descartar, Seguir editando; cambio de pestaña con borrador; Ctrl+Z/Ctrl+Y; guardar, cerrar y volver a abrir; exportar SRT.
- Completar la interfaz de filas visibles y selección de clip bidireccional. Después dividir/unir frases y edición de tiempos de segmento, preservando IDs y referencias. Entregar incrementos pequeños con pruebas independientes.
- **No tocar** el inspector Texto de Concat: reutilizarlo. No dar por terminadas las opciones de tiempo ni karaoke solo porque existen campos persistentes.
- Si la UI compila pero no puede probarse en una máquina Windows real, informar esa limitación y conservar el PR como borrador.

### Puerta B — Fase 4: karaoke fiable

- Obtener o alinear marcas de tiempo *reales* por palabra. Nunca distribuir uniformemente el tiempo como si fueran marcas exactas sin avisar.
- Probar Normal ↔ Progresivo ↔ Palabra ↔ Normal, sin perder datos individuales; cambios en dos clips diferentes; preview vs export.
- Corregir segmentación y el problema de párrafos largos antes de ampliar los efectos.

### Puerta C — Fase 5: animaciones y estilos

- Reutilizar el render de texto original; aplicar estilos/Glow también a títulos ordinarios. No duplicar inspectores.
- Animaciones con controles de duración y keyframes deshacibles, coincidentes entre vista previa y exportación.
- Perfil básico de memoria/latencia con 500 subtítulos antes de añadir más efectos.

### Puerta D — Fase 5.5: Voces IA

- Integración mediante proveedores intercambiables, empezando por un TTS local ligero con voces en español. Opciones avanzadas locales solo para máquinas capaces; API online como complemento opcional, sin credenciales compartidas ni costes impuestos.
- Revisar **la licencia concreta del motor y de cada modelo de voz**, las condiciones de distribución y el uso comercial antes de incorporarlo al instalador.
- Escribir → vista previa → insertar audio en pista → transcribir/subtitular audio final. La clonación de voz se limitará a casos autorizados.
- Conservar un modo de editor que funcione sin internet.

### Puerta E — Fases 6 y 7

- F6: CPU/GPU, CUDA como aceleración opcional; evitar congelar UI, escalabilidad en PCs modestas, instalador robusto y rendimiento medido.
- F7: diarización, subtítulos multidioma, exploración honesta de compatibilidad MOGRT, paneles ajustables.

## Política de protección del proyecto

1. PR por incremento, ramificado de la última base *validada*. No sustituir `main` ni las versiones de prueba funcionales por decisiones implícitas.
2. Guardar en documentación el criterio, las pruebas y la limitación de cada entrega.
3. Sin scripts que reescriban fuentes Rust/Slint durante CI. Cambios en archivos versionados.
4. Un workflow verde no sustituye una prueba manual con proyecto real.
5. No programar una función avanzada si la fase previa tiene un fallo de datos o interfaz sin resolver.
6. Mantener el inspector Texto original y separar inequívocamente títulos de subtítulos.
7. No introducir suscripciones obligatorias para funciones básicas.

## Entrega más próxima

Cerrar la validación automática del PR #9; si aparecen errores de compilación, corregirlos. Después hacer prueba Windows guiada sobre el instalador y atender observaciones, sin saltar a karaoke todavía.
