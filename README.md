# Estudio Joven — Concat con animaciones de texto

Base fijada a jub0t/Concat, commit `2756209a92766a4e4726999a51648349a272c159`.

## Compilar y descargar
En Actions ejecuta **Concat - Windows**. Al terminar con éxito, descarga **Concat-Estudio-Joven-Animaciones-windows-x86_64**, con instaladores EXE y MSI. El flujo también se ejecuta cuando cambia el parche.

## Animaciones (primera versión experimental)
Selecciona uno o varios bloques de texto en la línea de tiempo y abre **Texto → Animación de texto**. Elige Entrada y Salida entre Ninguna, Desvanecer, Deslizar, Zoom y Rebote. Ajusta las duraciones (0.05–3 segundos) y la intensidad. Reproduce desde el inicio del bloque para ver el efecto. Los cambios se aplican inmediatamente a todos los textos seleccionados y se pueden deshacer.

En clips cortos, entrada y salida reducen su duración proporcionalmente para evitar superponerse. Los parámetros se guardan con el proyecto; los fotogramas clave originales se conservan. La vista previa y la exportación usan la misma preparación de animación. Para quitar un efecto, selecciona Ninguna en ambas listas. El botón de estilo predeterminado también conserva estas opciones para futuros títulos y subtítulos.

## Fuente y pruebas
`patches/text-motion.patch` contiene todas las modificaciones sobre la fuente original. El workflow obtiene el código fijado, aplica el parche y ejecuta pruebas de tiempos, persistencia, composición con fotogramas clave y paridad entre vista previa/exportación antes de empaquetar. Además mantiene las pruebas de arranque y compatibilidad CPU del proyecto original.

La configuración original ya compiló correctamente; esta versión modificada requiere su propia compilación y prueba visual en Windows. El resultado de cada ejecución está en Actions.

Los modelos se descargan desde la aplicación. Las mejoras de karaoke y CUDA se describen abajo y requieren el instalador generado desde esta rama.

Concat conserva su nombre, créditos y licencia AGPL-3.0-or-later. Fuente: https://github.com/jub0t/Concat/tree/2756209a92766a4e4726999a51648349a272c159 . Los instaladores incluyen los avisos legales originales. FilmCraft permanece únicamente en el historial.

## Karaoke pop y transcripción CUDA (corrección experimental)

En Subtítulos selecciona **Karaoke pop**: una palabra por clip, amarilla con contorno y entrada de rebote. Funciona con voz o texto escrito. No es todavía resaltado progresivo de una frase completa ni una biblioteca de efectos CapCut. La selección se conserva al reabrir el panel. Cambiar de modo no transforma subtítulos existentes: elimínalos o deshaz su generación antes de generar de nuevo para no superponerlos.

La separación valida los tokens contra el texto original; si faltan palabras o los tiempos se superponen, recupera todas las palabras con tiempos proporcionales aproximados. Los tiempos de Whisper son experimentales. Se elimina el mínimo artificial de 0.2 segundos que hacía superponerse las palabras rápidas. Los textos escritos siempre usan tiempos aproximados.

En **Transcribir con** elige **Auto**, **CPU** o **GPU**. La compilación incluye el módulo dinámico CUDA 12.9.1 y sus bibliotecas, con kernels para RTX 20/30 y PTX para generaciones posteriores. Tu RTX 3070 Ti corresponde a la arquitectura 86. No necesitas instalar el Toolkit para usar el instalador; sí un controlador NVIDIA compatible. Auto elige una GPU registrada o CPU y vuelve a CPU si falla la inicialización de GPU. GPU exige un dispositivo disponible y muestra un error si no lo encuentra. El registro de la aplicación identifica el backend seleccionado y las posibles caídas a CPU; cambiar dispositivo recarga el modelo.

El artefacto nuevo se llama **Estudio-Joven-Karaoke-Pop-CUDA-windows-x86_64**. Las pruebas de GitHub validan separación, compilación y arranque sin NVIDIA; el rendimiento y la sincronización real necesitan una prueba con audio y la GPU del usuario. No se afirma que una compilación correcta pruebe CUDA en hardware.

**Oraciones** separa por puntuación, no identifica hablantes. **MOGRT** conserva el inspector de metadatos, sin reproducción de proyectos Adobe.
