# Estudio Joven — Ruta crítica de entregas

**Fecha de decisión:** 24 de octubre de 2026. La prioridad es una aplicación útil y comprobable, no la cantidad de funciones implementadas. Este plan coordina el registro maestro; no reemplaza sus 38 criterios.

**Nombre y estrategia de producto vigentes (24 oct 2026):** **JA Video Studio** será el nombre público final del editor para PC. **JA Connect** designa la futura función de comunicación y procesamiento entre una PC que actúa como servidor privado y clientes móviles. El usuario desea construir una **Suite** posteriormente, pero **primero exige terminar y estabilizar el editor de video Windows**; Android/Connect y otras apps solo tras autorización expresa. No renombrar paquetes, rutas, proyectos ni instaladores durante Fase 3C; planificar migración cuando corresponda y preservar los 38 compromisos.

## Orden de construcción y condiciones de paso

**Decisión vinculante 24 oct 2026 — versión móvil diferida:** completar, estabilizar y validar la versión PC/Windows en todas las puertas relevantes de esta ruta antes de iniciar trabajo Android. **Requiere autorización expresa del usuario cuando la versión PC esté estable y funcional.** No iniciar APK, CI Android ni rama móvil por ahora. La evaluación de la base Concat Android queda como antecedente de factibilidad, no como entrega. No agregar a los 38 pendientes ni fusionar PR sin autorización.

### Puerta A — Fase 3: estabilizar antes de extender

**Actualización F3C:** controles de segmentación y motor nativo implementados en commit `67d70c2`; requiere CI Windows #40130405239 y validación manual. CI F3B #40123969756 pasó y usuario confirmó selección/progreso. Corte proporcional dentro de frases Whisper es una estimación, NO alineación exacta por palabra. Persistencia de presets de proyecto, karaoke F4 y otros EJ permanecen abiertos.

**Fase 3B aprobada y codificada; pendiente CI/Windows:** previsualización de selección en vivo en Slint sin mutar Rust hasta release; eliminar animación duplicada de barra compartida. Validar clic, selección aditiva Shift, cancelación, pistas bloqueadas y porcentaje/anchura visual. No incluye segmentación ni karaoke. Ver continuidad.

**Estado actualizado 24 oct 2026:** el error de sintaxis Slint del CI #40112515736 quedó corregido en commit `ded75c8`. [Actions #40116367423](https://github.com/IsaacMPP/Prueba/actions/runs/40116367423) aprobó 171 pruebas Rust, Rust+Slint, build/smoke Windows e instaladores. **La puerta funcional sigue abierta:** el usuario probó Windows y detectó selección por recuadro sin resaltado previo al soltar, barra gráfica incongruente con el porcentaje de transcripción y subtítulos demasiado largos sin segmentación. Modos karaoke/configuraciones tipo Premiere aún no están integrados. Ver prueba manual anotada en `docs/CONTINUIDAD_CHATGPT.md`. No iniciar karaoke/Glow/TTS hasta estabilizar y validar en forma incremental.

- Verificar que el PR #9 compile Rust **y Slint**, pase pruebas, arranque y genere instalador. Si falla, arreglar esa misma rama antes de iniciar otra implementación.
- Probar manualmente en Windows: Whisper con voz en español; Generar / Editar; selección de frase; Aplicar, Descartar, Seguir editando; cambio de pestaña con borrador; Ctrl+Z/Ctrl+Y; guardar, cerrar y volver a abrir; exportar SRT.
- Completar la interfaz de filas visibles y selección de clip bidireccional. Después dividir/unir frases y edición de tiempos de segmento, preservando IDs y referencias. Entregar incrementos pequeños con pruebas independientes.
- **No tocar** el inspector Texto de Concat: reutilizarlo. No dar por terminadas las opciones de tiempo ni karaoke solo porque existen campos persistentes.
- Si la UI compila pero no puede probarse en una máquina Windows real, informar esa limitación y conservar el PR como borrador.

**Karaoke K1 iniciado con autorización nueva (24 oct 2026):** controles y metadatos de modos y tiempos por palabra aún sin render animado; necesita CI Windows. No declarar F4 completada mientras falten render común preview/export, alineación/corrección de palabras y pruebas reales. Prioridad de entrega: estabilizar K1, completar karaoke visual con export, terminar edición F3 y recién después F5/F6 de acuerdo con las dependencias. Preservar 38 EJ, inspector Texto, `main` y PR #9 draft.

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
