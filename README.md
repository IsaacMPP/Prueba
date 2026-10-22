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
