# Estudio Joven — Reconstrucción en código fuente nativo

**Estado:** Fase F1 en ejecución. **Rama de trabajo:** `feature/reconstruccion-fuente-nativa`.
**Base original:** Concat, commit `2756209a92766a4e4726999a51648349a272c159`, licencia AGPL-3.0-or-later.

## Decisiones aprobadas

1. Mantener Concat como editor base y conservar su inspector de Texto ORIGINAL.
2. Desarrollar Rust/Slint directamente sobre archivos fuente versionados. No ejecutar sustituciones de texto Python o `git apply` al compilar.
3. No mezclar el estado del generador con las propiedades de cada clip. La transcripción y los subtítulos son entidades separadas; ambos persistentes.
4. Los subtítulos serán clips de texto Concat identificados explícitamente con metadatos propios; jamás inferirlos por la pista con más títulos.
5. Un único origen de verdad para texto y tiempos de cada clip. La presentación (normal, karaoke progresivo, karaoke por palabra) pertenecerá a metadatos del subtítulo, mientras que fuente, color, contorno y animaciones seguirán en el inspector original.
6. Un cambio de selección debe actualizar el estado visual y no sobrescribir otros clips. Los borradores textuales/temporales se aplicarán o descartarán explícitamente. La apariencia conserva el commit existente de Concat.
7. Proyectos antiguos deben abrir sin pérdida; antes de cualquier migración destructiva se exigirán copias y pruebas.
8. Funciones avanzadas siguen pendientes: tiempos editables, estilos vinculados, Glow general, CUDA opcional/CPU, diarización, MOGRT.

## Fases y criterios de salida

| Fase | Resultado requerido | Estado |
|---|---|---|
| F0 | Auditoría y diseño base aprobados | Completado |
| F1 | Fuente de Concat en `src/`, sin scripts de sustitución en compilación; compilación y pruebas de regresión en Windows | En desarrollo |
| F2 | Persistencia de transcripción, pista subtítulos identificada y `CaptionMeta`, migraciones | Pendiente |
| F3 | Selección visible, aplicar/descartar, dividir/unir, edición de tiempos y undo | Pendiente |
| F4 | Karaoke por frase progresivo y palabra única con sincronización editable | Pendiente |
| F5 | Estilos vinculados, Glow general y animaciones | Pendiente |
| F6 | Whisper CUDA opcional, CPU, modelos, rendimiento y cancelación | Pendiente |
| F7 | Investigación diarización y MOGRT | Pendiente |

## Criterios esenciales de aceptación

- A → B → A conserva texto, modo, tiempos y apariencia individual.
- Editar y guardar transcripción → cerrar/reabrir → conserva correcciones, segmentación y tiempos.
- Seleccionar subtítulos de una pista excluye títulos/créditos ordinarios.
- Cambios masivos no reemplazan texto ni tiempos de otros elementos, y Ctrl+Z los revierte como unidad.
- Vista previa y exportación muestran la misma presentación de cada subtítulo.
- Una conversión normal → karaoke sin tiempos por palabra muestra un aviso de estimación.
- Sin CUDA, el editor y Whisper siguen funcionando en CPU.
- CI y pruebas manuales Windows deben pasar antes de fusionar. **Compilar no equivale a validar la experiencia de usuario.**

## Qué hacemos con los prototipos anteriores

Las ramas y PR #1–#5 permanecen como referencias aisladas; no se fusionan automáticamente. Las ideas y pruebas útiles se migrarán mediante módulos nativos nuevos, uno a uno. **No se copian los scripts `integrar-subtitulos.py`, `mejorar-subtitulos.py`, `karaoke_motor.py`, `transcripcion_primero.py`, `paneles_transcripcion.py` ni `modos_por_clip.py` a la rama limpia.**

## Procedencia, licencias y actualización

El árbol `src/` se incorpora sin reescribirlo desde el commit exacto citado. Preserva sus archivos originales de licencia y atribución. Cambios futuros deberán quedar en commits Rust/Slint normales, revisables por archivo y verificables con tests. No fusionar la rama hasta que tenga paridad funcional aprobada.
