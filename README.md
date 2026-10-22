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

No incluye todavía karaoke, sincronización por palabra ni aceleración CUDA. La transcripción conserva el motor CPU original. Los modelos se descargan desde la aplicación.

Concat conserva su nombre, créditos y licencia AGPL-3.0-or-later. Fuente: https://github.com/jub0t/Concat/tree/2756209a92766a4e4726999a51648349a272c159 . Los instaladores incluyen los avisos legales originales. FilmCraft permanece únicamente en el historial.

## Desarrollo experimental (rama feature/karaoke-dialogos-mogrt-cuda)
Esta rama aplica `scripts/ci/integrar-subtitulos.py` sobre el código fuente fijado de Concat y agrega al panel de subtítulos los modos **Normal**, **Oraciones** y **Karaoke**. El modo Oraciones separa frases por puntuación con tiempos proporcionales, NO identifica automáticamente personas distintas. Karaoke usa tiempos experimentales de tokens Whisper y crea clips de texto editables por palabra; no implementa todavía un resaltado progresivo dentro de una sola línea como CapCut.

**MOGRT:** `python scripts/tools/inspeccionar_mogrt.py archivo.mogrt` lista metadatos; no importa ni reproduce plantillas de After Effects. Los MOGRT arbitrarios exigen conversión o un motor compatible. **CUDA/RTX:** pendiente de integración y verificación. El paquete Windows actual mantiene Whisper CPU. Estas mejoras requieren que GitHub Actions compile y que se hagan pruebas visuales en Windows antes de considerarlas listas para uso general.

## Prueba de subtitulos sin CUDA (rama feature/subtitulos-capcut-sin-cuda)

La compilacion de esta rama conserva Whisper en **CPU**, deliberadamente, para aislar y verificar la subtitulacion antes de activar NVIDIA CUDA. Solo los artefactos de esta rama contienen estas mejoras.

**Donde:** selecciona un video con audio > Subtitulos / Captions > elige **Modo**:
- **Normal:** segmentos originales de Whisper, con la apariencia editable de Concat.
- **Frases:** bloques mas cortos, configurable Corto (24 caracteres), Medio (42), Largo (60), separados tambien por pausas y signos de puntuacion si hay datos suficientes. No es diarizacion automatica.
- **Karaoke pop:** un titulo por palabra; admite animacion Ninguna / Desvanecer / Deslizar / Zoom / Rebote suave, velocidad Rapida / Suave / Lenta. **No** resalta progresivamente cada palabra dentro de la misma frase (seria otro motor/efecto). El texto original no se pierde si Whisper devuelve tokens incoherentes: se estima el reparto de tiempos.

El panel ofrece **Color** (estilo guardado, blanco, amarillo, cian, coral, menta) y **Fuente** (estilo guardado, Hanken Grotesk, Cabinet Grotesk). Para fuentes importadas, sombras, contorno y cualquier color personalizado, edita un titulo desde el panel **Texto**, pulsa **Usar para nuevos titulos**, y en Subtitulos escoge **Estilo guardado**. Los titulos generados siguen siendo editables y varios seleccionados se pueden cambiar juntos. No se imponen colores sobre el estilo guardado. Para evitar sobreponer titulos existentes, deshaz o elimina los subtitulos anteriores **antes** de generar otros.

**Pruebas:** `scripts/ci/caption_words.rs` contiene pruebas de recuperacion de palabras, frases largas y signos de interrogacion; el workflow aplica `scripts/ci/mejorar-subtitulos.py`, ejecuta las pruebas, comprueba el codigo y construye el instalador. Una compilacion exitosa no demuestra por si sola que los subtitulos coincidan perfectamente con una cancion: eso requiere probar audio real en Windows.

No se ha agregado importacion real MOGRT ni aceleracion CUDA a esta rama.
