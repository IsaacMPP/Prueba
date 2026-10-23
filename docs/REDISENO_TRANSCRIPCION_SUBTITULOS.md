# Rediseño de Transcripción y Subtítulos — Estudio Joven

Rama de desarrollo: `feature/paneles-transcripcion-subtitulos`.
Base: `feature/transcripcion-karaoke-dinamico` (rama cuyo CI anterior compiló correctamente).
Estado: **fase de integración, revisión y compilación**. No fusionar sin pruebas visuales en Windows.

## Regla principal aprobada

**Todas las propiedades visuales se editan usando el Inspector Texto ORIGINAL de Concat.**
No crear otro sistema de fuente, tamaño, alineación, color, contorno, sombras o animaciones para subtítulos.
El panel de Transcripción corrige el texto reconocido; el de Subtítulos gestiona las piezas temporizadas, seleccionando el clip original de la línea de tiempo.

## Cambios implementados en esta iteración

- Nuevas pestañas Transcripción/Subtítulos dentro de la herramienta que ya existía.
- Lista de segmentos de transcripción con inicio, fin, texto y desplazamiento vertical.
- Selección de frase que lleva el playhead a su posición.
- Corrección individual de la frase. Si cambian las palabras y no se pueden mantener los tiempos, se avisa que se usarán estimaciones.
- Vista de subtítulos con lista desplazable de clips reales, ordenados por su inicio.
- Clic en subtítulo: la selección activa el clip real, posiciona el playhead y utiliza el **Inspector Texto existente**.
- Acción **Seleccionar todos los subtítulos de la pista**: aprovecha la edición múltiple que Concat ya tiene, sin reemplazar los textos ni duraciones.
- Quitados los selectores visuales duplicados (fuente, color, tamaño, posición y animación) del generador: esas propiedades siguen en Texto.
- Confirmación explícita de reemplazo antes de volver a transcribir.
- Aplicación determinista desde `scripts/ci/paneles_transcripcion.py` dentro del workflow, después de los parches previos.

## Limitaciones conocidas

- Aún está dentro del diálogo original, NO es todavía un panel acoplable/dockeable.
- La transcripción aún no se almacena como entidad permanente del proyecto: el caché actual es por sesión.
- Falta edición de tiempos por arrastre, división/unión de filas, selección por rango y sincronización bidireccional completa.
- Falta definir e implementar herencia vinculada de estilo por pista con excepciones por propiedad.
- Los dos formatos de karaoke acordados (progresivo y por palabra dentro del mismo clip-frase) necesitan trabajo de motor aparte.
- Glow general para cualquier texto está especificado pero **no** implementado en esta integración.
- CUDA y MOGRT siguen fuera de alcance.

## Pruebas de aceptación

1. Compilar la rama con GitHub Actions y ejecutar pruebas de Concat.
2. Transcribir audio real; editar una frase y generar subtítulos sin retranscribir.
3. Listas desplazables independientes con muchas frases.
4. Seleccionar un subtítulo de la lista y comprobar que el inspector de Texto original muestra sus controles.
5. Seleccionar la pista y ajustar el tamaño/color desde Texto: todos los clips de esa selección cambian, sus textos y tiempos permanecen.
6. Re-transcribir pide confirmación; no borra correcciones con el primer clic.
7. Importar/exportar SRT y comprobar que la versión anterior continúa funcionando.
8. Comprobar la visualización y el scroll reales en Windows, incluido espacio vertical del diálogo.

## Diseño de próxima iteración

- Extraer las dos vistas a paneles acoplables sin duplicar el inspector.
- Persistir estructura de transcripción en el proyecto, con migraciones y pruebas.
- Crear subtítulos mediante un cuadro específico con origen, segmentación, tipo de karaoke y destino.
- Estilos vinculados de pista y ediciones masivas con deshacer y excepciones individuales.
- Motor de karaoke por frase y Glow global desde el inspector actual.
