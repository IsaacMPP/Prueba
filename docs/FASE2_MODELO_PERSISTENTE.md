# Fase 2 — Datos persistentes de transcripción y subtítulos

## Alcance exacto del primer incremento

Se añaden estructuras tipadas y comandos de edición al modelo nativo Rust de Concat, **sin tocar el inspector Texto original**. No se cambia la interfaz todavía, ni se anuncian como funcionales las opciones de subtítulos del prototipo anterior.

- `TranscriptDocument`: identificador estable, línea de tiempo, clip de origen, idioma y segmentos editables con identificadores y tiempos de palabra.
- `CaptionMetadata`: identifica explícitamente a un clip de texto como subtítulo; guarda Normal, Karaoke progresivo o Karaoke por palabra, color activo, tiempos de palabra y vínculos opcionales a segmento/transcripción.
- Los tiempos de `TranscriptDocument` son relativos al audio del clip fuente. Los tiempos de `CaptionMetadata.words` son relativos al propio clip del subtítulo.
- El subtítulo mantiene la tipografía, posición, colores normales y animaciones de **Concat TextStyle**, sin otro editor.
- Los valores nuevos viven en espacios de nombres `estudioJovenTranscripts` (proyecto) y `estudioJovenCaption` (clip). Los documentos previos sin estos campos siguen abriendo y un título sin metadatos no es un subtítulo.
- Nuevos comandos `upsertTranscript`, `removeTranscript`, `setCaptionMetadata` pasan por la misma historia de deshacer/rehacer y guardado de Concat.
- Se rechazan tiempos NaN, invertidos y referencias inválidas a clips que no sean de texto; se protege la integridad del documento.
- Una consulta dedicada permite obtener solo los IDs de subtítulos de una línea de tiempo, **sin inferir por cantidad de títulos en una pista**.

## Pruebas integradas al propio código Rust

1. Guardar, deshacer, rehacer y reabrir una transcripción corregida.
2. Crear dos textos con presentaciones distintas y comprobar que los metadatos se conservan por separado después de guardar/reabrir.
3. Cambiar Karaoke a Normal sin borrar la información de palabra.
4. Excluir un título normal de la lista de subtítulos y rechazar un color inválido.
5. Rechazar tiempos inválidos sin cambiar el documento.

## Limitaciones de este incremento

- La captura de Whisper y los controles de la interfaz original aún **no invocan** estos comandos. Los prototipos antiguos siguen aislados. No atribuirles persistencia automática todavía.
- Aún no se implementa renderizado de karaoke sobre el nuevo modelo ni creación automática de IDs al importar SRT.
- Los textos antiguos no se convierten a subtítulos automáticamente: se requiere migración explícita cuando definamos las reglas.
- Separación/unión y sincronización completa del editor de subtítulos pertenecen a las próximas fases.

## Aceptación

Compilación Windows, pruebas del crate `concat-project`, smoke test, guardar/reabrir con pruebas y revisión visual posterior antes de cualquier merge. El código se edita como archivos Rust nativos en `src/`; no se ejecutan scripts de sustitución al compilar.
