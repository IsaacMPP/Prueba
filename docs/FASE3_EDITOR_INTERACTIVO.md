# Estudio Joven — Fase 3A: edición nativa de frases y subtítulos

**Estado:** primer incremento en rama aislada, pendiente de CI Windows y comprobación visual. **No fusionado en `main`.**

## Qué incluye este incremento

1. La herramienta existente **Captions** ahora ofrece páginas **Generar / Editar**, sin perder el generador Whisper ni importar/exportar SRT.
2. En **Editar** se elige **Transcripción / Subtítulos**. El desplegable de frases muestra texto y tiempo de inicio de los datos del proyecto real, por orden.
3. Al seleccionar un subtítulo, o una frase con subtítulo vinculado, se selecciona el **clip real** en la línea de tiempo. Su tipografía, color, posición y efectos siguen en el **inspector Texto original de Concat**.
4. Escribir crea un borrador local, no cambia el proyecto. **Aplicar cambios** envía los comandos nativos; **Descartar** conserva el documento y restaura el último texto aplicado.
5. Si se cambia de frase, pestaña o se intenta cerrar con un borrador pendiente, se ofrecen **Aplicar / Descartar / Seguir editando**. No se guardan borradores incompletos automáticamente ni se pierden por accidente.
6. Corregir una frase de transcripción aplica un **Batch**: guarda la transcripción y actualiza sus clips vinculados cuyo texto aún coincide con la frase original. Los clips individualmente retocados se respetan y no se sobrescriben.
7. Corregir un subtítulo modifica solo su contenido, preservando su estilo `TextStyle`, modo y tiempos de karaoke (todavía no renderizados).
8. Los cambios son deshacibles con Ctrl+Z a través de `Studio::apply` y se incluyen en el guardado/autoguardado normal de Concat.
9. El editor usa los IDs de transcripción, segmento y clip como identidad; las filas solo representan su posición visual.

## Pruebas introducidas

- Borrador detectado sin mutar el valor aplicado.
- Filas largas abreviadas en la lista.
- Corrección conjunta de transcripción y subtítulo como una sola unidad de deshacer, con cierre/reapertura del documento.
- Se mantienen las pruebas anteriores de persistencia, protección SRT y metadatos por clip.

## Límites explícitos de Fase 3A

- Primera interfaz utiliza el mismo panel flotante original de Captions, con selector de frases, **no** una lista completa con varias filas visibles simultáneamente o paneles acoplables.
- Edición visual de tiempos de inicio/fin, dividir/unir frases, diarización, selección múltiple y los modos visuales de karaoke siguen pendientes.
- Las transcripciones Whisper tienen tiempos por frase; todavía no existe alineación exacta por palabra.
- El panel de títulos antiguo no se sustituye ni se duplica; ajustes visuales siguen en él.
- Falta comprobar en Windows con un video real la sincronización entre selección, vista previa, exportación SRT, cierre/reapertura y undo.
- Los proyectos Concat anteriores que solo contienen títulos sin metadatos no se clasifican automáticamente como subtítulos.

## Condición de aceptación

Ninguna fase se declara completa por la compilación solamente. Se requiere CI Windows (pruebas Rust y Slint, build, smoke, instalador) y revisión manual para detectar estados de teclado/foco y confirmación en la UI.
