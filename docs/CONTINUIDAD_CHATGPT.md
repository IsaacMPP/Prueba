# ESTUDIO JOVEN — CONTINUIDAD ENTRE CONVERSACIONES (LEER PRIMERO)

## REDISEÑO DE SUBTÍTULOS — INCREMENTO R2, UNA PALABRA CENTRADA (25 OCT 2026, CI PENDIENTE)

El usuario reiteró que en modo **Palabra** solo debe verse una palabra en pantalla y no toda la oración. La implementación K2 resaltaba pero no eliminaba las palabras restantes. Se reconstruyó el efecto técnico `concat.karaoke-highlight` sin crear clips nuevos en el **proyecto**:

- El shader WGSL lee cuatro parámetros animados `word_x`, `word_y`, `word_half_w`, `word_half_h`; en modo **Palabra** toma únicamente el rectángulo del vocablo activo en el raster original, oculta el resto por alfa y lo traslada al **centro de la misma imagen/título**, donde sigue aplicándose el desplazamiento general y la transformación del subtítulo. En pausas o antes de que suene una palabra no muestra el título. En **Progresivo** conserva toda la frase y colorea las palabras pronunciadas. **Normal** no recibe efecto.
- `concat-host/src/titles.rs` añade rectángulos normalizados al `Art` cacheado en memoria y derivados del sidecar ya disponible en disco. Genera el transform por palabra con claves de salto para el efecto GPU, a partir de los `CaptionMetadata.words` existentes; imagen base de texto, línea de tiempo, IDs de clip y estilo fuente siguen intactos. Si el pintor y el reloj discrepan en conteo de palabras, no aplica el efecto hasta corregir el material: no se inventan alineaciones.
- Las rutas `Titles::clips_live` y `Titles::clips` comparten el filtro, la textura y posiciones derivadas. El test existente de equivalencia monitor/export comprueba además `word_x` y parámetros del modo una palabra. No se incluyen motores duplicados por plataforma.
- **Validación obligatoria:** CI Windows Rust, Slint, tests, carga de shader WGSL, smoke/Ivy Bridge e instalación, después revisión visual REAL sobre metraje español, palabras largas/cortas, fondo/transparencia, saltos y exportación. **No declarar completado antes de estas pruebas.** Debe evaluarse aparte el caso de subtítulos con placa/fondo, multirenglones y estilos especiales. La integración automática por audio real y un master style permanentemente vinculado siguen pendientes; R1 es copia en lote.

**Archivos R2:** `src/src/crates/concat-effects/packages/concat.karaoke-highlight/effect.toml`, `effect.wgsl`; `src/src/crates/concat-host/src/titles.rs`; `src/src/crates/concat/locales/en.json` y `es.json` (texto explicativo). No cambiar `main`, PR #9 ni EJ-001..EJ-038.

---


## REDISEÑO DE SUBTÍTULOS — INCREMENTO R1, AUTORIZADO (25 OCT 2026; VALIDAR EN CI Y WINDOWS)

**Problemas observados por el usuario en Windows con metraje real:** seleccionar Karaoke Palabra **todavía deja visible la oración completa**; los controles de tiempos parecían reiniciarse, ajustar una palabra rechazaba el cambio sin comportamiento útil, navegar entre frases restablecía la palabra seleccionada y «Crear tiempos estimados» sobreescribía correcciones; falta un flujo de pista y edición similar a Adobe Premiere. El usuario autorizó explícitamente «procede» para **reconstruir el módulo de edición de subtítulos**, sin improvisar parches ni modificar el resto del editor.

**Incremento R1 propuesto en fuente, no declarado aprobado:** 
- El modelo `concat-project::caption_data` valida **no solapamiento real** de relojes consecutivos; introduce `move_caption_word_boundary` que mueve junto el límite compartido cuando dos palabras se tocan, mantiene pausas y no modifica nada si el nuevo límite es imposible (con tests).
- La UI de karaoke distingue **crear tiempos ausentes** de **recalcular sobrescribiendo**. Si ya hay tiempos, el botón de estimación no los reemplaza; una acción explícita de recalcular exige confirmación en la UI. Las palabras seleccionadas en el editor se recuerdan por ID de subtítulo al navegar y al reabrir panel, en lugar de volver a palabra 1.
- El editor añade un control **«Aplicar apariencia a esta pista de subtítulos»**, que copia tipografía/apariencia, modo Normal/Progresivo/Palabra y color desde el subtítulo actual a los demás subtítulos **identificados en esa misma pista**, mediante un **solo Command::Batch** deshacible. No modifica el texto de los otros clips, ni los relojes por palabra/alineación, ni títulos ordinarios ni otras pistas. Es una copia puntual: **NO** es aún un estilo de pista vinculado permanentemente al estilo maestro de Premiere. Hay pruebas de no pérdida de palabras, textos, títulos y Undo.
- `save_karaoke` verifica el estado persistido y muestra error si el comando falló.
- UI `ui/dialogs/captions.slint` + cableado `ui/app.slint`, `src/lib.rs`, traducciones `locales/en.json`, `locales/es.json`. Archivos de modelo: `concat-project/src/caption_data.rs`, `concat/src/panes/captions.rs`.

**Puertas abiertas:** R1 requiere pasar CI Windows Rust+Slint y pruebas reales antes de afirmar que guarda correctamente; el flujo tipo Premiere completo (panel fijo en el editor, pista de subtítulos con estilo maestro real, límites de frase arrastrables, división/unión, snapping, sincronización por audio, karaoke 1 palabra realmente centrada en previsualización y exportación) **SIGUE PENDIENTE**, no confundir R1 con rediseño terminado. El render anterior K2 es prototipo de resaltado, no cumple el modo una palabra sola. No introducir otros módulos en paralelo. Los 38 EJ se mantienen, inspector Texto original, `main` y PR #9 draft siguen protegidos.

---


## CORRECCIÓN AUTORIZADA DE ARRANQUE K2 — PALABRA RESERVADA WGSL (24 OCT 2026)

El usuario autorizó **corregir el fallo identificado** del karaoke, sin ampliar alcance. [Windows CI #40151622185](https://github.com/IsaacMPP/Prueba/actions/runs/40151622185) finalizó `failure` en **Smoke test (Windows)** a pesar de compilar y pasar **172 pruebas Rust de concat-project**. El ejecutable abortó al cargar el catálogo de efectos incorporados, porque el shader `src/src/crates/concat-effects/packages/concat.karaoke-highlight/effect.wgsl` declaró `let active`, pero `active` es nombre reservado en WGSL (`catalogue.rs:1000`). Se sustituye únicamente esa variable por `word_is_active` en su declaración y referencia. Ni la lógica del efecto, ni tiempos de palabra, ni visuales, ni shaders ajenos se modifican.

**Estado:** cambio de código preparado para su CI Windows posterior. NO afirmar que K2 arrancó, exportó o fue probado con metraje real hasta confirmar el nuevo run, smoke, instaladores y validación de GPU en Windows. PR #9 continúa draft, `main` intocado, inspector Texto original intacto, 38 compromisos EJ-001..EJ-038 preservados. K1 aprobada en [#40150719478](https://github.com/IsaacMPP/Prueba/actions/runs/40150719478); K2 requiere validación independiente. Sigue pendiente centrar la palabra, alineación real, y demás prioridades documentadas.

---


## INCREMENTO K2 — RENDER KARAOKE GPU COMPARTIDO (24 OCT 2026 — CI Y WINDOWS REALES PENDIENTES)

**Autorización de usuario:** ampliar a karaoke visual y demás compromisos; desarrollo incremental sin parches y sin fusiones. Después de K1 se preparó K2 (motor visual) usando **la infraestructura de efectos WGSL original de Concat**:

- Paquete interno `concat.karaoke-highlight`: lee el mapa `reveal_order(uv)` ya horneado por `concat-text`; no reimplementa tipografía, inspector ni generador de clips. Lee reloj de palabra como un parámetro animado `cursor`, colorea los vocablos completados en **Progresivo** y únicamente la palabra activa en **Palabra**. Normal sigue sin efecto.
- `concat-host/src/titles.rs` convierte las marcas persistentes `CaptionMetadata.words` en claves temporales de `AppliedFilter` **al aplanar el mismo clip de texto**, tanto para `Titles::clips_live` (monitor) como `Titles::clips` (export). Este filtro **NO** se persiste como un efecto adicional del proyecto: el proyecto mantiene un único clip editable por subtítulo; las claves se derivan de sus marcas guardadas. Se añade después de efectos de color del clip.
- La cadena **se omite** si faltan relojes, el texto cambió en cantidad de palabras o hay tiempos solapados/fuera de rango. Un video sin sincronizar conserva apariencia Normal y sigue siendo editable.
- El `concat.karaoke-highlight` se excluye del catálogo visible de filtros, porque es una implementación técnica interna, no una opción creativa arrastrable.
- Tests Rust de `concat-host` exigen que los clips de monitor y export den **exactamente el mismo filtro y claves**, con un solo clip por subtítulo. El catálogo de efectos valida todos los WGSL incorporados.

**Estado preciso:** K2 está preparado en fuente pero **NO puede declararse aprobado hasta CI Rust+Slint, pruebas GPU, smoke Windows e inspección real de exportación**. Incluso con CI verde, **modo Palabra solo destaca el vocablo en su lugar dentro de la frase**; el requisito EJ-017 de recolocarlo *centrado* sigue abierto. No existe forced alignment real ni adaptación fina a sílabas; marcas estimadas conservan su condición explícita y requieren corrección de oído. Las placas/fondos de estilo de texto pueden requerir tratamiento específico para que solo el relleno de los glifos sea coloreado. Compatibilidad GPU/CPU y portabilidad necesitan pruebas. No confundir con cierre F4.

**Archivos K2:** nuevos `src/src/crates/concat-effects/packages/concat.karaoke-highlight/{effect.toml,effect.wgsl}`; `src/src/crates/concat-host/src/titles.rs`, `src/src/crates/concat/src/studio.rs` (ocultar paquete técnico); `ui/dialogs/captions.slint`, `locales/en.json`, `locales/es.json`. Continúa K1. Conservar exactamente EJ-001..038, inspector original Texto, rama activa, PR #9 draft, `main` intacto. No realizar Android, JA Connect ni LOG sin permiso.

---


## NUEVA AUTORIZACIÓN — MODOS KARAOKE Y EDICIÓN AVANZADA (24 OCT 2026)

**Usuario autorizó ampliar el desarrollo** a modos karaoke y pendientes del editor («bien ahora integra los modos karaoke y todo lo demás porfa»). Se mantiene metodología: diseñar y desarrollar incrementos nativos validados, sin hacks, sin tocar `main`, inspector Texto ni fusionar PR #9. La solicitud no anula la puerta de calidad: karaoke completo exige **render funcional idéntico en monitor y export**, marcas por palabra verificables y Windows manual; no declarar terminado por mera persistencia de metadatos.

**Incremento K1 preparado en fuente — PENDIENTE CI/Windows:** en Generar/Editar › Subtítulos hay modos **Normal, Progresivo y Palabra** por subtítulo (metadatos `CaptionPresentation` ya existentes); selección de cuatro colores de resaltado; creación **voluntaria y señalizada de tiempos estimados** por palabra; edición manual de inicio y fin, validada dentro del clip y entre palabras sin solapes; estado de alineación `Unaligned/Estimated/Edited` persistido con `serde(default)` para proyectos antiguos. **Edited = parcialmente editado, no validado exacto.** Cada modificación se guarda en la única historia de deshacer del proyecto; modo A→B→A no elimina color ni tiempos. Cambiar texto de un subtítulo o su frase transcrita invalida los antiguos relojes sin perder modo/color, en el mismo lote undoable. No se crean clips extra por palabra ni se modifica el inspector original.

**Estado estricto:** la interfaz de modos **todavía NO altera el dibujo** del video ni la exportación; render karaoke progresivo y palabra (EJ-016/017) sigue PENDIENTE. Tampoco hay forced alignment de voz (EJ-005/018), backend GPU ni animations implementadas en este incremento. No etiquetar karaoke como terminado. Preview/render común, corrección de relojes con audio real y prueba Windows real son puertas obligatorias.

**Código K1:** `src/src/crates/concat-project/src/caption_data.rs`, `src/src/crates/concat/src/panes/captions.rs`, `src/src/crates/concat/src/panes/caption_editor.rs`, `src/src/crates/concat/src/lib.rs`, `src/src/crates/concat/ui/dialogs/captions.slint`, `src/src/crates/concat/ui/app.slint`, `src/src/crates/concat/locales/{en,es}.json`. Pruebas modelo guardado/reapertura/undo y conservación/invalidez al cambiar texto, estimación proporcional. **Prioridad siguiente:** revisar CI Rust/Slint, corregir bloqueos detectados; luego integrar render de karaoke en el núcleo común monitor/export y comprobarlo, antes de iniciar otros módulos. Mantener los 38 EJ y documentos.

---


## CORRECCIÓN AUTORIZADA DE FASE 3C — VALIDAR CI (24 OCT 2026)

El usuario autorizó expresamente **solo** reparar el fallo de compilación, idiomas y errores posteriores que revele CI, sin añadir funciones nuevas. La ejecución [#40134001688](https://github.com/IsaacMPP/Prueba/actions/runs/40134001688) falló ANTES de compilar Rust/Slint, en `python scripts/locales.py --check`: `gone: captions.oneTitlePerPhrase`. Las etiquetas nuevas de la segmentación estaban fijadas en español.

**Corrección acotada:** convertir etiquetas de F3C a `I18n.t`, añadir claves en catálogos inglés/español y retirar `captions.oneTitlePerPhrase` de todos los idiomas existentes. NO tocar el motor de reconocimiento, lógica de segmentación, algoritmos de renderizado, karaoke, inspector Texto, `main`, ni código Android/JA Connect. El validador admite traducciones faltantes en idiomas adicionales y utiliza inglés de respaldo.

**Siguiente tarea:** verificar nuevo CI Rust+Slint, Windows smoke y artefacto; reparar en la misma rama cualquier error de compilación demostrado, dentro del alcance autorizado. No declarar aprobado hasta obtener resultado real. PR #9 sigue draft y 38 EJ inalterados.

---


## IDENTIDAD DEFINITIVA Y ALCANCE — JA VIDEO STUDIO (24 OCT 2026)

**Decisión explícita del usuario:** el nombre **final y público del editor de video** será **JA Video Studio**. El nombre técnico/de trabajo histórico `Estudio Joven` y las rutas, paquetes, ramas y documentos existentes pueden mantenerse **temporalmente** para evitar cambios disruptivos durante la estabilización. **No renombrar todavía el código fuente, paquetes, identificadores, instaladores o rutas de datos sin planificación y autorización explícita**, con migración de proyectos, compatibilidad y pruebas.

**JA Connect** (antes denominado provisionalmente *Estudio Joven Connect*) es el nombre definitivo del sistema/concepto futuro de conexión PC ↔ dispositivos móviles: el equipo Windows podría procesar localmente transcripciones y otras tareas pesadas para dispositivos autorizados, devolviendo resultados editables. **No es el nombre final de la aplicación** ni debe añadirse a esta fase. Requiere diseño de seguridad, autenticación, transferencia de audio, enrutamiento de trabajos y compatibilidad, solo cuando se retome móvil.

**Visión posterior:** crear una **Suite** de herramientas relacionadas; por ahora **no definir productos nuevos, ni abrir líneas de desarrollo, ni decidir el nombre comercial de la Suite**. Prioridad exclusiva: finalizar **JA Video Studio para Windows**, completar las funciones pendientes, superar CI y las pruebas reales, asegurar instalación/guardado/exportación/rendimiento y estabilizar. **Solo entonces**, con autorización del usuario, abordar la versión móvil/Connect y, más adelante, otros productos de la Suite.

**Alcance actual invariable:** continuar la Fase 3C PC y su validación; mantener los 38 compromisos EJ-001 a EJ-038, el inspector Texto original, la rama activa y PR #9 en borrador. No tocar `main`, no fusionar PR y no iniciar Android o Connect prematuramente.

---


## DECISIÓN VIGENTE — ANDROID / VERSIÓN MÓVIL SE POSPONE (24 OCT 2026)

**Decisión explícita del usuario:** no implementar ni compilar una APK de Estudio Joven por ahora. **Primero concluir, estabilizar y probar funcionalmente Estudio Joven para PC/Windows**: subtítulos, edición, karaoke cuando corresponda, guardado/reapertura, exportación, rendimiento y el resto de compromisos priorizados. **Solo cuando la versión PC esté estable y funcional y el usuario autorice expresamente retomar móvil**, iniciaremos la adaptación y validación Android. No iniciar ramas móviles, CI Android, APK ni nuevos compromisos de desarrollo en este momento.

**Factibilidad ya investigada, sin implementar:** la base Concat tiene `src/src/crates/concat-android`, interfaz táctil Slint en `src/src/crates/concat/ui/phone` y scripts `src/src/scripts/*mobile*.sh`. Son una base, no una APK Estudio Joven ya validada. Cuando corresponda, realizar auditoría de compatibilidad Android ARM64, SDK/NDK, bibliotecas multimedia y carga de modelos, interfaz tablet horizontal y pruebas reales sin alterar la fuente estable PC. **Android es una etapa posterior, no se agrega como compromiso n.º 39.**

Esta decisión prima sobre cualquier sugerencia anterior de preparar APK en paralelo. La Fase 3C PC sigue siendo el trabajo activo y sus verificaciones aún deben confirmarse. `main` y el inspector **Texto original** no se modifican, no fusionar PR #9 sin autorización y conservar los **38 compromisos EJ-001 a EJ-038**.

---


## FASE 3C — SEGMENTACIÓN CONFIGURABLE IMPLEMENTADA, VALIDACIÓN EN CURSO (24 OCT 2026)

**Código integrado:** [commit 67d70c2](https://github.com/IsaacMPP/Prueba/commit/67d70c20f614b572ed6af400158c8b9288025d1c), rama `feature/fase3-editor-transcripcion-subtitulos`, PR #9 sigue draft y `main` intacta. El usuario confirmó manualmente las dos correcciones F3B (selección y barra). CI F3B [#40123969756](https://github.com/IsaacMPP/Prueba/actions/runs/40123969756) **success**.

**Implementado en fuente, todavía sin validación Windows F3C:** motor nativo independiente `src/src/crates/concat/src/panes/caption_segmentation.rs` con tests Rust; conexión en `panes/captions.rs` y `panes/mod.rs`; controles Slint en `ui/dialogs/captions.slint` y cables `ui/app.slint`, `src/lib.rs`. Reglas: una/dos líneas o una palabra, caracteres máximos por línea (42 por defecto), máximo de palabras (12), duración mínima orientativa (0.7s), máxima (6.0s) y separación en frames (0 por defecto). Se subdivide cada intervalo de Whisper conservando todas las palabras; cada subtítulo tiene ID de segmento y comando de lote deshacible. No se modificó el inspector Texto original.

**Validación:** [Actions #40130405239](https://github.com/IsaacMPP/Prueba/actions/runs/40130405239) evalúa **el commit integrado** `67d70c2`, observado `pending` inicialmente. [#40129996254](https://github.com/IsaacMPP/Prueba/actions/runs/40129996254) comenzó tras el commit del módulo aislado `4271eb9` y **no valida la integración**; se lanzó antes de agrupar los cambios. No generar nuevas ejecuciones hasta analizar #40130405239; si falla, revisar el primer error real.

**Límites pendientes:** tiempo individual por palabra **no es real**: el motor estima los cortes proporcionalmente dentro de los segmentos con tiempo conocido de Whisper; nunca inventar precisión, extender fuera del audio ni truncar palabras. Mínimo de duración orientativo si los límites de longitud lo impiden; palabras larguísimas sin espacios permanecen completas. Ajustes se retienen al reabrir panel en la misma sesión, no se guardan aún como preset de proyecto. Karaoke real F4, regenerar subtítulos existentes, división/unión manual, edición exacta de tiempos y comparación de preview/export pendientes.

**Próximas comprobaciones:** CI Rust y Slint, build Windows, smoke/instalador; después video real español, límites de dos líneas/caracteres, modo palabra vs karaoke (son conceptos distintos), selección/corrección por ID, Undo/Redo, guardar/reabrir y SRT. Los **38 compromisos** permanecen abiertos conforme a cada criterio, sin declarar la Fase 3 cerrada.

---


## FASE 3B — IMPLEMENTACIÓN DE CORRECCIONES VISUALES (24 OCT 2026)

**Autorización:** el usuario pidió «procede» después de aprobar dos correcciones aisladas: selección por recuadro visible mientras se arrastra y barra de progreso que corresponda al porcentaje mostrado. Los IDs involucrados son **EJ-012** (resaltado en la línea de tiempo) y **EJ-029** (presentación de progreso de transcripción); el resaltado de las filas del editor **EJ-006** continúa pendiente.

**Código fuente de esta entrega:**
- `src/src/crates/concat/ui/timeline/lanes.slint`: `Clip.selection-highlighted` recibe una previsualización puramente visual durante el arrastre en el área de la línea de tiempo. El cálculo considera cruce temporal y de pista, clips bloqueados, Shift aditivo y un umbral de 4 px para distinguir clic. Rust sigue haciendo la selección definitiva en `band-selected` al soltar; cancelar descarta la previsualización sin cambiar el proyecto.
- `src/src/crates/concat/ui/primitives/modal.slint`: se elimina la segunda animación de `width` del relleno de `Progress`. El porcentaje y el ancho proceden directamente de `shown`, que ya se interpola por tiempo. La estimación interna de `Pace` y los reportes parciales de Whisper **no** se convierten por ello en progreso exacto.

**Validación automática iniciada:** [Actions #40123969756](https://github.com/IsaacMPP/Prueba/actions/runs/40123969756) (workflow Windows, SHA de fuente `2acd74f9487aa77b788c675773f1256b397ed056`), **in_progress** al registrar. Solo se lanzó la ejecución automática generada por el commit de código; no ejecutar una segunda validación ni afirmar éxito antes de consultar el estado final. Este commit adicional de documentación no altera `src/**` y no debería iniciar otro workflow.

**Comprobaciones necesarias:** compilación Rust+Slint y smoke Windows; probar manualmente arrastre normal, Shift aditivo, ratón cancelado, clips de pistas bloqueadas, clic sin arrastrar, barra al transcribir y coherencia geométrica con el porcentaje. No marcar requisitos como completados hasta CI + prueba Windows. **No se incluyó segmentación tipo Premiere ni karaoke en este incremento.** Los 38 pendientes siguen vigentes, inspector Texto original intacto, `main` intacto y PR #9 en borrador.

---


## PRUEBA MANUAL WINDOWS — 24 OCT 2026 (OBSERVACIONES DEL USUARIO)

**El usuario comprobó en Windows** que una transcripción genera subtítulos y que la interfaz Generar/Editar y el inspector Texto original están presentes. Esto es evidencia parcial, **no** completa la prueba manual Fase 3A ni confirma exportación/reapertura/undo o comportamiento del karaoke.

**Hallazgos nuevos con capturas:**

1. **Selección de clips por recuadro NO se resalta durante el arrastre** (se aplica al soltar). Confirmado en fuente: `src/src/crates/concat/ui/timeline/lanes.slint`, callback `band-selected` y `band := TouchArea` (confirmación al soltar), más `src/src/crates/concat/src/lib.rs` al manejar `on_band_selected`. **Comportamiento deseado:** previsualización visual continua durante el arrastre, con selección definitiva al soltar, Shift aditivo, clips bloqueados excluidos y cancelación reversible. No confundir con selección de una fila del editor. Relación EJ-012/EJ-006.
2. **La barra de transcripción luce mucho más corta que el 51% indicado** en la captura. Fuente observada: `ui/dialogs/captions.slint` dibuja texto desde `bar.shown`; `ui/primitives/modal.slint` calcula ancho desde ese valor y además anima `width` 280 ms, mientras el valor cambia por `animation-tick()`. **Hipótesis a verificar:** animación de ancho que se retrasa/reinicia frente al valor mostrado; no afirmar causalidad hasta probar. Diferenciar porcentaje medido vs estimado por `panes/pace.rs`. Relación EJ-029 (UX de progreso).
3. **Subtítulos demasiado extensos.** Confirmado: `src/src/crates/concat/src/panes/captions.rs` genera un clip directamente por cada segmento Whisper, sin limitar caracteres/líneas/duración; `TranscriptSegment.words` se guarda vacío. Hace falta segmentar sin inventar marcas exactas por palabra. Relación EJ-013/EJ-020/EJ-010/EJ-011.
4. **Configuración deseada semejante a Premiere:** longitud máxima en caracteres (ejemplo visto: 42), disposición una o dos líneas o palabra, duración mínima y máxima, separación entre subtítulos, segmentación por pausas/frases, edición de inicios/finales, vista previa, opciones conservadas por proyecto. Los valores son ejemplos de referencia, no defaults aprobados. «Frases» es una regla de segmentación, NO un modo de karaoke.
5. **Modos Normal, Karaoke progresivo y Karaoke por palabra** deben ser seleccionables por clip, con tiempos revisables y persistencia, respetando el inspector Texto original. El modelo guarda metadatos preliminares; **render y alineación por palabra siguen pendientes** (EJ-004/EJ-005/EJ-016–EJ-019).

**Secuencia propuesta (no implementada aún):** primero previsualización de selección y concordancia visual de progreso (dos correcciones aisladas); segundo motor de segmentación configurable con pruebas de duración/identidad, luego UI de presets en la herramienta original; tercero completar edición por filas y tiempos; cuarto karaoke una vez asegurada alineación por palabra y paridad entre vista previa/exportación. No cambiar `main` ni fusionar PR #9; conservar 38 compromisos. Para funciones nuevas seguir análisis/diseño/autorización antes de escribir código.

---

## ACTUALIZACIÓN HISTÓRICA — FASE 3A COMPILA Y CI WINDOWS APROBADO (24 OCT 2026)

- **Rama:** `feature/fase3-editor-transcripcion-subtitulos`. **Código corregido:** [commit `ded75c8`](https://github.com/IsaacMPP/Prueba/commit/ded75c8d675788dc3c60ba59337e2f72962afd05). Se editaron **solo ocho separadores** `;` → `,` en las líneas 61–68 de `src/src/crates/concat/ui/dialogs/captions.slint`, dentro de `CaptionsSheetData`.
- **Compilación de validación, única para esta corrección:** [GitHub Actions #40116367423](https://github.com/IsaacMPP/Prueba/actions/runs/40116367423), estado **completed / success**. Se comprobaron **171 pruebas Rust aprobadas, 0 fallidas**, compilación Rust+Slint, build Windows x86_64, smoke Windows, emulación Ivy Bridge, análisis de instrucciones, generación de instaladores y subida del artefacto.
- La ejecución anterior [#40112515736](https://github.com/IsaacMPP/Prueba/actions/runs/40112515736) sí falló por sintaxis Slint; sus 171 pruebas Rust pasaron. La sección histórica de abajo describe ese fallo **antes** de la corrección.
- **Artefacto disponible:** [Concat-Estudio-Joven-Animaciones-windows-x86_64](https://github.com/IsaacMPP/Prueba/actions/runs/40116367423/artifacts/12571342945), archivado en GitHub Actions; contiene dos instaladores (EXE y MSI), **no equivale a una validación manual**. La ejecución aprobada compiló commit `ded75c8`; el HEAD posterior contiene únicamente documentación adicional. No se identificaron nuevos errores de compilación en ese run.
- **Próxima acción obligatoria:** probar en Windows con video/audio español y proyecto real el editor de frases (Aplicar/Descartar/Seguir editando), selección, inspector Texto original, Undo/Redo, persistencia, exportación SRT y render. Después continuar con los EJ pendientes de Fase 3; no declarar completa la fase por tener CI verde. No relanzar compilaciones sin cambios de fuente.
- Los **38 compromisos EJ-001 a EJ-038** siguen vigentes. No tocar el inspector **Texto original**, no modificar `main`, ni fusionar **PR #9** (borrador) sin autorización. Este commit de documentación no contiene archivos bajo `src/**` y no debería disparar una segunda compilación en el workflow configurado.

---

## HISTORIAL — ERROR REAL DETECTADO ANTES DE LA CORRECCIÓN (24 OCT 2026)

**PRIORIDAD ABSOLUTA DEL PRÓXIMO CHAT: corregir el error en Slint, sin agregar funciones nuevas ni modificar main.**

**Evidencia verificada directamente en GitHub Actions:**
- [Ejecución fallida #40112515736, run #31](https://github.com/IsaacMPP/Prueba/actions/runs/40112515736), commit evaluado \`6909022458b07d0419b743cd2e23da678ce477df\`.
- Resultado: **failure** en compilación de la aplicación (\`concat\`, \`build.rs\`, \`ui/app.slint\`), **exit code 101**. No es una cancelación gris.
- Previamente, **171 pruebas del modelo Rust PASARON y 0 fallaron** (\`test result: ok. 171 passed; 0 failed\`). Eso no valida la interfaz.
- Mensaje repetido del compilador Slint: \`Expected ','. Use ',' instead of ';' to separate fields in a struct\`.
- Archivo exacto en la rama F3: \`src/src/crates/concat/ui/dialogs/captions.slint\`, líneas **61 a 68**, dentro de \`export struct CaptionsSheetData\`.
- Los campos introducidos se encuentran escritos como \`editor-tab: int;\`, \`editor-kind: int;\`, \`editor-items: [string];\`, \`editor-selected: int;\`, \`editor-text: string;\`, \`editor-dirty: bool;\`, \`editor-confirm: bool;\`, \`editor-message: string;\`. **La estructura Slint exige comas \`,\` en vez de punto y coma \`;\`**.
- Comprobado también leyendo el archivo fuente de la rama, no solo el log. Esta es la **primera causa bloqueante demostrada**, pero al repararla podrían aparecer más errores aún ocultos.

### Corrección autorizada como siguiente objetivo (sin ejecutar en esta conversación)

1. En nueva conversación: verificar una vez el HEAD de \`feature/fase3-editor-transcripcion-subtitulos\`, el contenido actual de \`captions.slint\` y los últimos workflows. La rama tenía HEAD \`e684dbec99d814dc0f564f23b33a1032b874b8c4\` al investigar; HEAD cambia con cada actualización de documentación.
2. Editar **solo** las ocho declaraciones de campos en la estructura \`CaptionsSheetData\` para sustituir los \`;\` por \`,\`; NO cambiar puntos y coma de propiedades/callbacks en otras partes, donde sí pueden ser válidos.
3. Inspeccionar las demás declaraciones nuevas de la interfaz para coherencia estructural; no rediseñar el editor ni agregar funciones para resolver un error de sintaxis.
4. Crear **un solo commit de código bien delimitado** y disparar **una** nueva validación GitHub Actions en la rama. Evitar sucesivos pushes que cancelen las ejecuciones pendientes.
5. Si el nuevo workflow falla, diagnosticar el **primer error nuevo del log** (Slint o Rust) y corregirlo en la fuente nativa. No anticipar problemas no observados.
6. Exigir pruebas Rust, compilación Slint, build Windows, smoke test e instalador correctos; después pedir prueba manual con video real para considerar F3A utilizable. PR #9 sigue **draft**; NO fusionar a main ni entregar instalador F3 sin validar.
7. Al terminar, actualizar este documento y \`REGISTRO_MAESTRO.md\` con ejecución, SHA, resultado real y siguientes pendientes.

**Nota de procedencia:** el run #31 compiló el commit \`69090224\`. Los commits posteriores hasta \`e684dbec\` eran documentación; se verificó que el bloque con los ocho \`;\` aún existía en la rama cuando se detectó el fallo.

### Mensaje corto para pegar en un nuevo chat (comenzar directamente con el error)

> Continuemos **Estudio Joven**, repo \`IsaacMPP/Prueba\`, rama \`feature/fase3-editor-transcripcion-subtitulos\`, PR #9. Lee primero \`docs/CONTINUIDAD_CHATGPT.md\` y \`docs/REGISTRO_MAESTRO.md\`. **Ya hay un error confirmado** en [Actions #40112515736](https://github.com/IsaacMPP/Prueba/actions/runs/40112515736): Slint falla al compilar \`src/src/crates/concat/ui/dialogs/captions.slint\` líneas 61–68 porque dentro de \`CaptionsSheetData\` ocho campos tienen \`;\` y deben llevar \`,\`. Las 171 pruebas Rust pasaron; la interfaz no compiló. Verifica HEAD y el log, corrige solamente el problema de sintaxis sin parches ni cambios a main, ejecuta un único workflow y resuelve cualquier nuevo error revelado. Después actualiza el registro y mantén PR #9 en borrador hasta las pruebas Windows reales.

---


> **Punto de recuperación preparado el 24 de octubre de 2026 (America/Cancun).**
> Es un *resumen de referencia*, NO prueba de que GitHub mantenga hoy estos mismos estados. Siempre consultar GitHub antes de cambiar archivos.

## 0. Instrucción para cualquier conversación nueva

El usuario desarrolla **Estudio Joven**, un editor de video de escritorio para Windows basado en **Concat**. El repositorio autorizado es **https://github.com/IsaacMPP/Prueba**.

**Primero, sin escribir código:**
1. Acceder a GitHub y leer **este documento**, [REGISTRO_MAESTRO.md](REGISTRO_MAESTRO.md), [RUTA_CRITICA_ENTREGAS.md](RUTA_CRITICA_ENTREGAS.md) y [FASE3_EDITOR_INTERACTIVO.md](FASE3_EDITOR_INTERACTIVO.md) en la rama de trabajo.
2. Comprobar la rama y SHA actuales, el estado del **PR #9** y los últimos workflows de Actions; nunca asumir que una compilación pendiente sigue igual.
3. Comparar resultados con el estado de referencia de abajo; informar lo confirmado, lo pendiente y el siguiente paso.
4. Continuar desde la última versión **validada**; un PR en borrador o un pipeline verde no significan automáticamente una función terminada.
5. Si el usuario autoriza implementar, trabajar en Rust/Slint **directamente en archivos fuente versionados**, con pruebas y una rama/PR aislados; no empezar módulos nuevos mientras el anterior tenga errores críticos sin resolver.

La conversación previa llegó a su límite de longitud. **No pedir al usuario que vuelva a contar todo el proyecto: este archivo y sus documentos complementarios son el punto de partida.**

## 1. Identidad, objetivos y restricciones

- Producto: **Estudio Joven**, editor de video completo, no una aplicación independiente de subtítulos.
- Base técnica: Concat, escritorio Windows, Rust + Slint en la fuente nativa. Concat original: commit \`2756209a92766a4e4726999a51648349a272c159\`.
- La intención es ser útil tanto en computadoras medianas como en equipos potentes; el usuario dispone de una **RTX 3070 Ti**, pero el programa NO debe exigir NVIDIA.
- Se requiere transcripción local Whisper, editor visual integrado, subtítulos configurables, karaoke, animaciones similares a CapCut, importación/exportación SRT, más adelante voces TTS y otras funciones avanzadas.
- **Usar siempre el inspector Texto ORIGINAL de Concat** para tipografía, color, contorno, sombra, efectos y Glow futuro. NO crear un segundo editor de apariencia.
- Distinguir un título de un subtítulo mediante **metadatos explícitos**, no por la cantidad de clips de texto en una pista.
- Los subtítulos y transcripciones deben persistir al guardar/reabrir, con identificadores estables, modificaciones individuales y deshacer.
- «Frases» es una **configuración de segmentación**, no un modo visual equivalente a Normal/Karaoke.

## 2. Reglas no negociables acordadas con el usuario

1. **Analizar → Diseñar → Presentar para revisión → Obtener autorización → Implementar → Compilar → Probar.**
2. El usuario puede delegar el **orden de prioridades**, pero eso no autoriza a introducir funciones ajenas al alcance vigente sin diseño.
3. **Nada de parches acumulativos:** si algo está mal estructurado, refactorizar o rehacer correctamente. Nunca encadenar scripts Python que reescriban Rust/Slint durante build.
4. Reutilizar módulos y controles existentes; evitar duplicar estados, inspectores, renderizadores o sistemas de selección.
5. Mantener \`main\` y el instalador previamente probado intactos. **No fusionar PR ni reemplazar una versión sin autorización explícita.**
6. Conservar todos los pendientes con identificador; actualizar el registro en cada cambio. No marcar «terminado» solo porque compiló.
7. Verificar compatibilidad con proyectos anteriores, comportamiento Windows real y paridad entre vista previa y exportación.
8. Si GitHub Actions falla, inspeccionar el log y corregir la fuente responsable; no generar parches improvisados ni crear múltiples ejecuciones consecutivas sin necesidad.
9. Declarar las limitaciones con precisión: tests automáticos, compilación, prueba manual y funcionalidad entregada son niveles diferentes.

## 3. Estado de GitHub verificado en el punto de recuperación

Repositorio: **https://github.com/IsaacMPP/Prueba**

| Elemento | Referencia | Estado observado el 24-10-2026 |
|---|---|---|
| \`main\` | \`a7739f2f1010765d457fac4cb46fbdd5397db63c\` | Rama principal sin fusionar la reconstrucción |
| Fuente nativa — Fase 1 | [PR #6](https://github.com/IsaacMPP/Prueba/pull/6), rama \`feature/reconstruccion-fuente-nativa\` | Draft, CI de compilación base Windows superado |
| Modelo persistente — Fase 2A | [PR #7](https://github.com/IsaacMPP/Prueba/pull/7), rama \`feature/fase2-datos-transcripcion-subtitulos\` | Draft; tests del modelo aprobados |
| Whisper + metadatos/SRT — Fase 2B | [PR #8](https://github.com/IsaacMPP/Prueba/pull/8), rama \`feature/fase2-whisper-conexion-nativa\` | Draft; [Actions #40059410498](https://github.com/IsaacMPP/Prueba/actions/runs/40059410498) **success**, 170 pruebas, build/smoke/instalador |
| Editor de frases — Fase 3A | [PR #9](https://github.com/IsaacMPP/Prueba/pull/9), rama **\`feature/fase3-editor-transcripcion-subtitulos\`** | Draft, sin fusionar. HEAD documentado: \`3c670bf31b67ddeda2d07279504bcc9aa6d26399\` |
| Fase 3 Actions | [#19](https://github.com/IsaacMPP/Prueba/actions/runs/40110783642) | \`in_progress\` en \`Build\` para SHA anterior \`a3207a78...\` |
| Última ejecución Fase 3 visible | [#31](https://github.com/IsaacMPP/Prueba/actions/runs/40112515736) | \`pending\` para SHA \`69090224...\`; aún NO se confirmó un build verde de la última UI |
| Ejecuciones #20–#30 Fase 3 | Actions | \`cancelled\` en espera; gris **no** equivale a error Rust/Slint |

**Importante:** el HEAD \`3c670bf...\` contiene commits posteriores de **documentación** a la ejecución #31. Consultar workflows, HEAD y cambios más recientes de nuevo; el estado puede haber cambiado. No asegurar que el PR #9 ya compiló hasta disponer de prueba.

Las ramas antiguas [PR #1–#5](https://github.com/IsaacMPP/Prueba/pulls) contienen prototipos de karaoke, animaciones y rediseño, pero **NO se fusionan ni se copian a ciegas** a la reconstrucción nativa.

## 4. Arquitectura y archivos para localizar trabajo

En \`feature/fase3-editor-transcripcion-subtitulos\`:
- \`src/src/crates/concat-project/src/caption_data.rs\`: \`TranscriptDocument\`, segmentos, palabras, \`CaptionMetadata\`, modos normal/progresivo/por palabra, identificación y exportación filtrada.
- \`src/src/crates/concat-project/src/commands/mod.rs\` y \`commands/subtitles.rs\`: cambios nativos deshacibles y creación de subtítulos identificados.
- \`src/src/crates/concat/src/panes/captions.rs\`: generación Whisper, SRT, conexión con el editor.
- \`src/src/crates/concat/src/panes/caption_editor.rs\`: selección por ID, borradores, cambio de destino, Aplicar/Descartar y actualización de textos.
- \`src/src/crates/concat/ui/dialogs/captions.slint\`: pestañas Generar/Editar y Transcripción/Subtítulos.
- \`src/src/crates/concat/ui/app.slint\` y \`src/src/crates/concat/src/lib.rs\`: conexión de callbacks UI ↔ Rust.
- \`src/src/crates/concat/src/studio.rs\`: selección del clip real y uso del inspector Texto original.
- \`.github/workflows/compilar-fuente-nativa-windows.yml\`: compilación Windows desde fuente versionada, sin cadena de scripts de parcheo.
- \`docs/FASE2_MODELO_PERSISTENTE.md\`, \`docs/FASE2B_WHISPER_NATIVO.md\`, \`docs/FASE3_EDITOR_INTERACTIVO.md\`: detalles por incremento.

### Lo que ya existe en Fase 3A (código, no versión entregada)
- Panel Generar/Editar, subpestañas Transcripción/Subtítulos y un **selector de frases**; aún NO una lista simultánea de filas estilo Premiere.
- Edición por borrador y botones Aplicar, Descartar y Seguir editando.
- Confirmación al salir/cambiar de selección con cambios no aplicados.
- Selección del clip de subtítulo real en la línea de tiempo, conservando el inspector Texto original.
- Corrección de una transcripción y actualización de subtítulos vinculados cuyo texto no fue personalizado, con operaciones de deshacer.
- Correcciones recientes para verificar que Aplicar realmente persista y para que Descartar consulte la versión actual tras Undo/Redo.
- Pendiente verificar que todo esto **compile** en Windows y funcione con un video real.

## 5. Qué falta — prioridades estrictas

**Próxima tarea inmediata: corregir el error confirmado de sintaxis de Slint (arriba), verificar compilación y estabilizar Fase 3. NO comenzar karaoke ni voces IA aún.**

1. Consultar el último workflow de PR #9 y los logs. Si falló: diagnosticar y corregir la fuente Rust/Slint de esa rama. Evitar múltiples pushes simultáneos que cancelen runs pendientes.
2. Al pasar CI: revisar instalador y pruebas manuales Windows con audio real (transcribir, seleccionar, editar, aplicar, descartar, cambiar frase/pestaña con borrador, Ctrl+Z/Ctrl+Y, guardar/cerrar/reabrir, exportar SRT). **No afirmar haber probado Windows manualmente sin evidencia.**
3. Completar Fase 3: lista con filas **visibles simultáneamente y scroll** en Transcripción y Subtítulos, selección visual clara y bidireccional con la línea de tiempo, edición de inicio/fin, dividir/unir, selección múltiple por pista, reglas de subtitulación (caracteres, líneas, duración), buscar/reemplazar, cambios individuales y masivos.
4. Compatibilidad: proyectos viejos con clips de texto sin \`CaptionMetadata\` no deben etiquetarse automáticamente; diseñar migración/clasificación segura. No perder SRT ni textos.
5. **Fase 4:** modo Normal, karaoke progresivo y por palabra; tiempo exacto por palabra (estimado debe marcarse como estimado), colores configurables, conservados A → B → A y tras guardado; resolver frases largas y preview/export.
6. **Fase 5:** animaciones estilo CapCut, Glow para cualquier texto, estilos vinculados con excepciones individuales, copiar/pegar atributos y duración editable.
7. **Fase 5.5:** Voces IA TTS locales (Kokoro/Piper o alternativa validada), opciones más expresivas y APIs externas optativas, vista previa e inserción directa en pista; revisar licencias de modelos/voces y hardware.
8. **Fase 6:** CUDA opcional y fallback CPU, autodetección modelos Whisper, tareas no bloqueantes, pruebas de fluidez y recursos con 500 subtítulos y PCs medianas.
9. **Fase 7:** diarización de voces, pistas de idiomas, evaluar MOGRT real (no prometer soporte completo) y paneles acoplables.

**El inventario completo y con criterios de aceptación de los 38 requisitos está en [REGISTRO_MAESTRO.md](REGISTRO_MAESTRO.md).** La priorización y puertas de calidad están en [RUTA_CRITICA_ENTREGAS.md](RUTA_CRITICA_ENTREGAS.md).

## 6. Requisitos de UX que originaron la Fase 3

El usuario enseñó una captura del editor donde los subtítulos aparecían en una lista oscura, sin indicar qué fila estaba seleccionada; cambiar el modo Normal/Frases/Karaoke no aplicaba cambios a un clip existente. Quiere:
- Transcripción y Subtítulos en pestañas, ambos con filas visibles, selección resaltada y scroll.
- En Transcripción, corregir el texto original antes de crear o modificar subtítulos.
- En Subtítulos, poder seleccionar una fila y modificar ese **subtítulo específico** sin afectar otros.
- Botones para Aplicar/Descartar y cambios pendientes; acción en lote similar a Premiere.
- Cada texto conserva su modo (normal, progresivo, por palabra), su color, tiempos y animaciones, incluso después de cambiar la selección o cerrar/reabrir.
- **No duplicar el panel de propiedades Texto de Concat**. Glow se agregará al editor común para TODOS los textos en la fase correspondiente.
- El usuario valora una interfaz limpia, profesional, usable y sin controles duplicados.

## 7. Plan de trabajo de la próxima conversación

1. Abrir este documento y los otros documentos maestros desde GitHub.
2. Consultar **en vivo** PR #9, acciones más recientes, rama HEAD, diferencias con el snapshot y logs si hay un fallo.
3. Presentar un resumen corto: estado confirmado, tareas pendientes, riesgo principal, siguiente cambio puntual.
4. **No comenzar una fase futura si Fase 3 aún falla.** Si la tarea solicitada es corregir la compilación, trabajar solo sobre la causa de ese fallo y sus pruebas.
5. Después de cualquier cambio, actualizar \`docs/REGISTRO_MAESTRO.md\` y este punto de recuperación si cambian decisiones o estado. No crear varias fuentes contradictorias.
6. Para futuras conversaciones: usar siempre la **última versión** de este archivo en GitHub, no los SHAs históricos que contiene.

## 8. Mensaje listo para pegar en un chat nuevo

> Quiero continuar mi proyecto **Estudio Joven** en el repositorio GitHub **IsaacMPP/Prueba**. Antes de programar, abre y lee el archivo \`docs/CONTINUIDAD_CHATGPT.md\` de la rama \`feature/fase3-editor-transcripcion-subtitulos\`, junto con \`docs/REGISTRO_MAESTRO.md\`, \`docs/RUTA_CRITICA_ENTREGAS.md\` y \`docs/FASE3_EDITOR_INTERACTIVO.md\`. Consulta en vivo el PR #9, el HEAD de GitHub y la compilación más reciente. Dime dónde estamos y qué falta, distinguiendo lo compilado de lo probado en Windows. Sigue nuestras reglas: diseñar antes de programar, no parchar, conservar el inspector Texto original, mantener main intacta y no olvidar ningún pendiente. Primero verifica el estado; después continuamos con la fase que corresponda, sin adelantar funciones.

---

**Mantenimiento:** actualizar cuando termine una compilación relevante, una prueba manual, un hito o cambie una decisión técnica. Si un enlace/branch deja de existir, localizar el documento por ruta en la rama sucesora o utilizar la copia descargada. Ningún estado histórico sustituye una verificación actual.