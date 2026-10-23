# Estudio Joven — Reconstrucción con fuente nativa

Editor de video de escritorio Windows basado en [Concat](https://github.com/jub0t/Concat), conservando créditos y licencia AGPL-3.0-or-later.

**Esta rama es de desarrollo y NO es el instalador funcional de subtítulos existente.** Las versiones experimentales siguen disponibles en `feature/paneles-transcripcion-subtitulos` y `feature/modos-subtitulos-por-clip`, sin fusionarlas.

## Arquitectura

- Código real versionado en `src/` (snapshot verificable del commit Concat `2756209a92766a4e4726999a51648349a272c159`).
- Cambios de Estudio Joven futuros realizados directamente en los archivos Rust/Slint, con pruebas y commits revisables.
- **Sin aplicar parches ni scripts Python de reemplazos durante la compilación.**
- Se mantiene el inspector Texto original. Transcripción, subtítulos, modo visual y estilos tendrán responsabilidades separadas.
- Cada fase tendrá pruebas antes de mezclarla con el editor usable.

## Fases

Consulta [Plan de reconstrucción](docs/PLAN_RECONSTRUCCION.md).

La incorporación del fuente original la realiza un workflow **de una sola ejecución** para esta rama, eliminando la dependencia de descargar Concat y reescribir su código en cada build. La compilación de fuente limpia se verificará por separado antes de introducir cambios experimentales.

## Derechos de autor

Concat y sus componentes conservan su licencia y atribuciones originales dentro de `src/`. Estudio Joven respeta los requisitos de redistribución y publicación de código fuente de AGPL-3.0-or-later.
