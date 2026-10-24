# Fase 2B — Conectar Whisper, guardado y subtítulos identificados

**Estado:** implementación en rama experimental; requiere CI y prueba Windows. No fusionada en main.

## Flujo que implementa esta iteración

1. El usuario abre Captions y elige un clip de audio y un modelo Whisper (se conserva por ahora el flujo del formulario original de Concat).
2. Whisper reconoce frases en un hilo de trabajo; el resultado se guarda en un `TranscriptDocument` con ID propio y segmentos temporizados. Whisper upstream entrega tiempos **por segmento**, no por palabra: `words=[]`, sin fingir karaoke preciso.
3. En el **mismo lote de edición** se insertan los clips de texto de subtítulos como `Command::AddCaptionClip`, con metadatos explícitos y referencia a su transcripción/segmento.
4. Cada ejecución se registra como una nueva versión de la transcripción para no sobrescribir correcciones previas. Deshacer revierte juntos transcripción nueva y subtítulos generados.
5. Los subtítulos creados desde guion y SRT también se identifican. Los títulos/créditos normales mantienen `AddTextClip` y siguen siendo títulos.
6. La exportación SRT usa la función única `caption_cues` del modelo: **solo clips etiquetados como subtítulos**. Con título seleccionado, no supone que su pista sea de subtítulos.
7. Al duplicar un texto en la línea de tiempo, si es subtítulo se copian sus metadatos y presentación, sin mezclar instancias.
8. Si el usuario elimina, mueve, recorta o cambia de medio/audio el clip de origen mientras Whisper transcribe, se descarta el resultado y se evita crear subtítulos desincronizados.

## Pruebas

- Test en `concat-project`: una transcripción y un subtítulo se guardan juntos, se reabren, y se deshacen juntos.
- Test en `concat-project`: exportar SRT excluye títulos aunque compartan pista.
- Test en `concat-project`: recortar un clip no borra accidentalmente su identidad de subtítulo.
- Tests anteriores: A/B/A conserva modos y tiempos; título sin metadatos nunca pasa por subtítulo; datos inválidos son rechazados.
- Ejecutar Windows CI y pruebas manuales de transcripción y exportación antes de fusionar.

## Limitaciones y trabajo futuro

- **No existe todavía una vista completa de transcripción editable con Aplicar/Descartar** en esta rama. Eso pertenece a Fase 3 y todavía requiere conectar cambios de texto a los comandos persistentes.
- El panel conserva la generación automática original de Concat, pero los resultados se guardan como entidades persistentes para poder editarlos sin volver a ejecutar Whisper en la siguiente fase.
- Todavía no hay karaoke renderizado en esta rama; los campos de presentación son de datos, no efectos visuales activos.
- Repetir una transcripción conserva versiones anteriores y crea nuevos clips, igual que la generación de Concat puede superponer subtítulos. Más adelante el panel ofrecerá elegir entre conservar/reemplazar sin sorpresas.
- Proyectos antiguos con textos sin metadatos se abren, pero no se clasifican automáticamente como subtítulos ni se exportan como tales. Se requiere una acción explícita de clasificación o migración para no incluir títulos ordinarios.
- No se fusionan cambios de los PR #1–#5 directamente ni se introducen scripts que parchen el código.

## Regla de avance

La prueba verde significa que compila y pasa controles automatizados; **no demuestra la exactitud de Whisper en audios reales ni la experiencia UX completa**. Probar con video real, guardar y reabrir en Windows antes de terminar el requisito.
