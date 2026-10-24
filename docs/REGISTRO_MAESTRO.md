# Estudio Joven — Registro maestro de 38 compromisos

**Actualizado:** 24 de octubre de 2026 (Fase 3A: corrección Slint y CI Windows aprobados; validación manual pendiente). **Fuente de verdad para las siguientes fases.**

**Error histórico confirmado:** [GitHub Actions #40112515736](https://github.com/IsaacMPP/Prueba/actions/runs/40112515736) terminó en **failure**. Pasaron 171 pruebas Rust, pero el compilador Slint rechazó ocho declaraciones separadas con `;` en `src/src/crates/concat/ui/dialogs/captions.slint`, líneas 61–68: `CaptionsSheetData` necesita `,` como separador de campos. **Primero corregir ese error de sintaxis; luego compilar y revisar nuevos errores si aparecen.** No hay build F3 aprobado ni prueba manual, no fusionar PR #9. Leer [CONTINUIDAD_CHATGPT.md](CONTINUIDAD_CHATGPT.md).

**Estado de corrección (CI aprobado):** commit [ded75c8](https://github.com/IsaacMPP/Prueba/commit/ded75c8d675788dc3c60ba59337e2f72962afd05) cambia únicamente los ocho campos de `CaptionsSheetData` de `;` a `,`. La única compilación para ese cambio, [Actions #40116367423](https://github.com/IsaacMPP/Prueba/actions/runs/40116367423), finalizó **success**: 171 pruebas Rust / 0 fallidas, Slint+Rust, build Windows x86_64, smoke, Ivy Bridge, escaneo ISA, EXE/MSI y artefacto subido. **Falta prueba manual Windows con video real y cierre funcional de los EJ de Fase 3. PR #9 sigue draft; `main` e inspector Texto original intactos.**

**CI F3B:** [Actions #40123969756](https://github.com/IsaacMPP/Prueba/actions/runs/40123969756), iniciada automáticamente por commit `2acd74f9487aa77b788c675773f1256b397ed056`; **in_progress** en el último chequeo. No dar por aprobada hasta consultar resultado final, smoke e instaladores. 

**Fase 3B — cambios fuente en validación:** previsualización de selección por recuadro durante el arrastre en `lanes.slint` y barra con relleno sin animación duplicada en `modal.slint`; aprobados como alcance por el usuario. Pendiente resultado CI y prueba manual Windows. **Sin karaoke ni segmentación Premiere todavía.**

**Prueba manual parcial (24 oct 2026):** con video real en Windows el usuario confirma generación de transcripción/subtítulos y disponibilidad del inspector Texto original. Reportó selección por recuadro que solo se pinta al soltar, porcentaje de transcripción (ej. 51%) que no coincide visualmente con barra, clips con párrafos largos sin reglas configurables de líneas/caracteres/duración, y ausencia de modos karaoke. Diagnóstico técnico, fuentes y criterios en [CONTINUIDAD_CHATGPT.md](CONTINUIDAD_CHATGPT.md). **No afirmar Fase 3 completa ni karaoke implementado**; falta corregir estos problemas y ejecutar pruebas funcionales adicionales. Los 38 compromisos se conservan.\n\n**Fase 3C en fuente, pendiente CI y prueba Windows:** [commit 67d70c2](https://github.com/IsaacMPP/Prueba/commit/67d70c20f614b572ed6af400158c8b9288025d1c), motor de segmentación nativo + controles tipo Premiere. CI del commit integrado [#40130405239](https://github.com/IsaacMPP/Prueba/actions/runs/40130405239) observado inicialmente pendiente; el run anterior #40129996254 compilaba solo el módulo y no constituye validación F3C. El usuario confirma F3B y CI #40123969756 success. **Los tiempos subdivididos se estiman; karaoke y persistencia de presets siguen pendientes.**

Estados: **En validación** = CI o pruebas pendientes; **Prototipo previo** = existe solo en ramas experimentales (NO en fuente limpia); **Conservado** = función base de Concat; **Pendiente** = no integrado o no completado; **Investigación** = requiere factibilidad.

| ID | Función | Prioridad | Estado en fuente limpia | Fase | Criterio para cerrar |
|---|---|---|---|---|---|
| EJ-001 | Rust/Slint versionado, sin scripts de parcheo | P0 | Compilación Windows y smoke CI aprobados; PR pendiente sin fusionar | F1 | CI nativo y smoke Windows exitosos |
| EJ-002 | Transcripción persistente con IDs estables | P0 | CI Windows F2B aprobado: 170 pruebas; falta prueba con video real | F2 | Guardar/cerrar/abrir conserva texto y tiempos |
| EJ-003 | Identificar subtítulos, separados de títulos/créditos | P0 | Generador y SRT conectados; tests aprobados, prueba real pendiente | F2 | Lotes/SRT excluyen títulos normales |
| EJ-004 | Modo independiente por subtítulo | P0 | Modelo y duplicación del clip conectados; render karaoke/UI pendientes | F2–F4 | A/B/A y reapertura sin cambios cruzados |
| EJ-005 | Palabras temporizadas y estado de alineación | P0 | Tiempos tipados en modelo; edición y alineación pendientes | F2–F4 | Tiempos guardados, revisables y corregibles |
| EJ-006 | Resaltado de fila seleccionada | P0 | Selector de frase activo; lista simultánea pendiente; prueba Windows inicial evidenció resaltado de selección por recuadro solo al soltar (revisar EJ-012) | F3 | Selección visible en ambas listas |
| EJ-007 | Sincronía panel ↔ línea de tiempo | P0 | Panel selecciona clip real; sincronización inversa pendiente | F3 | Selección bidireccional con el clip exacto |
| EJ-008 | Aplicar/Descartar/cambios pendientes | P0 | F3A: sintaxis Slint corregida en ded75c8; CI Windows #40116367423 aprobada; lógica aún sin validar manual/visualmente | F3 | No perder borradores al navegar |
| EJ-009 | Deshacer/rehacer atómico individual y en lote | P0 | Pendiente | F3 | Ctrl+Z revierte solo la operación elegida |
| EJ-010 | Edición por frase de texto y tiempos | P0 | Texto conectado; tiempos siguen pendientes | F3 | Cambiar sin volver a transcribir |
| EJ-011 | Separar y unir frases | P0 | Pendiente | F3 | Preservar palabras y relojes |
| EJ-012 | Ctrl/Shift, selección de toda la pista | P0 | F3B CI y selección/barra confirmadas en Windows; Ctrl/Shift por pista aún pendientes | F3 | Solo subtítulos identificados y resaltado inmediato |
| EJ-013 | Generador configurable: caracteres/líneas/duración | P1 | Prototipo previo; en fuente nativa los segmentos Whisper se convierten sin dividir a clips, largos en prueba Windows | F3–F4 | Pruebas de segmentación y vista previa |
| EJ-014 | Importación y exportación SRT | P1 | Exportación filtrada por identificación explícita; CI y prueba manual pendientes | F3–F4 | Round-trip por pista explícita |
| EJ-015 | Buscar/reemplazar en transcripción | P1 | Pendiente | F3 | Correcciones y deshacer válidos |
| EJ-016 | Karaoke progresivo resaltando palabra activa | P1 | Prototipo previo | F4 | Video real y exportación consistentes |
| EJ-017 | Karaoke por palabra centrada, sin 1 clip por palabra | P1 | Prototipo previo | F4 | Posición correcta sin saltos |
| EJ-018 | Corrección manual de tiempos por palabra | P1 | Pendiente | F4 | Sincronización editable y persistente |
| EJ-019 | Conservar ajustes al cambiar modo | P0 | Prototipo previo | F4 | Normal ↔ karaoke no borra tiempos ni color |
| EJ-020 | Evitar truncado silencioso por límite de 12 palabras | P1 | Pendiente; párrafos demasiado largos comprobados manualmente | F4 | Frases largas y segmentación explícita |
| EJ-021 | Inspector Texto ORIGINAL para todos los clips | P0 | Conservado | F1–F5 | Ningún inspector duplicado |
| EJ-022 | Cambiar atributos sin modificar palabras | P1 | Conservado/parcial | F5 | Edición múltiple probada |
| EJ-023 | Estilos vinculados con excepciones por atributo | P1 | Pendiente | F5 | Modificar pista respeta excepciones |
| EJ-024 | Copiar/pegar estilo y presets sin copiar texto | P1 | Pendiente | F5 | Atributos independientes |
| EJ-025 | Glow para cualquier título/texto | P1 | Pendiente | F5 | Funciona en títulos y subtítulos |
| EJ-026 | Animaciones estilo CapCut con control de duración | P1 | Prototipo previo | F5 | Preview/export y undo coherentes |
| EJ-027 | Whisper CUDA NVIDIA con alternativa CPU | P1 | Pendiente | F6 | Benchmark en GPU y PC sin GPU |
| EJ-028 | Detección automática de modelos Whisper | P1 | Pendiente | F6 | Selección sin buscar rutas |
| EJ-029 | Transcripción no bloqueante y cancelable | P1 | Ejecución en trabajador y cancelación conservadas; F3B elimina doble animación del ancho de barra, CI/prueba Windows pendientes; progreso estimado sigue siendo estimado | F6 | UI responde mientras procesa |
| EJ-030 | Fluidez con 500 subtítulos | P1 | Pendiente | F4–F6 | Perfil de RAM y latencia medido |
| EJ-031 | Diarización de personas que hablan | P2 | Investigación | F7 | Prototipo contrastado con audio real |
| EJ-032 | Subtítulos multidioma en pistas independientes | P2 | Pendiente | F7 | No sobrescribir subtítulos originales |
| EJ-033 | MOGRT real: investigación de importación/conversión | P2 | Investigación | F7 | Propuesta técnica realista |
| EJ-034 | Paneles acoplables y ajustables | P2 | Pendiente | F7 | Usables en varias resoluciones |
| EJ-035 | Compatibilidad y migración de proyectos antiguos | P0 | Pendiente | F2 | Archivo viejo abre sin pérdidas |
| EJ-036 | Pruebas Windows CPU/GPU y máquinas modestas | P1 | Pendiente | Todas | Hardware documentado y pruebas reales |
| EJ-037 | Exportación coherente con vista previa | P0 | Conservado/parcial | Todas | Comparaciones visuales y automatizadas |
| EJ-038 | Voces IA locales y proveedores TTS opcionales | P2 | Planificado, sin código implementado | F5.5 | Voz en español, escucha previa, pista de audio, licencias verificadas, sin exigir API ni internet |

## Reglas obligatorias

1. Ningún pendiente desaparece del registro por comenzar otra función.
2. Antes de programar, indicar los IDs de esta tabla que se modifican y sus criterios de aceptación.
3. No cambiar **Pendiente/Prototipo** a **Terminado** sin diseño aprobado, código Rust/Slint integrado, test automático y prueba funcional de Windows cuando corresponda.
4. No confundir una rama experimental que compila con una función entregada a usuarios.
5. No fusionar `feature/reconstruccion-fuente-nativa` a `main` sin paridad de requisitos aprobados.
6. No introducir scripts que alteren código fuente por cadenas en el pipeline. Modificar archivos nativos directamente.
