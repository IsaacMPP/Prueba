# Estudio Joven — base Concat

Este repositorio sustituye la compilación anterior de FilmCraft por Concat para Windows x64.

## Compilar
En Actions, selecciona **Concat - Windows** y **Run workflow**. Al terminar correctamente, descarga el artefacto **Concat-windows-x86_64**, que contiene los instaladores EXE y MSI.

La primera compilación se inicia al incorporar esta configuración. El flujo conserva las dependencias verificadas y las pruebas de arranque del proyecto original.

## Código fuente
El flujo descarga `jub0t/Concat` en el commit fijo `2756209a92766a4e4726999a51648349a272c159`, correspondiente al ZIP Concat-main.zip revisado. El código completo se obtiene durante la compilación, no está duplicado en este repositorio.

Fuente: https://github.com/jub0t/Concat/tree/2756209a92766a4e4726999a51648349a272c159

La receta de compilación se adapta de `.github/workflows/build-app.yml` de ese commit. Concat conserva su nombre y créditos. El código original indica licencia AGPL-3.0-or-later; el empaquetado incluye LICENSE y THIRD_PARTY_NOTICES.md del proyecto.

## Estado
Esta es la base original de Concat. Todavía no incluye nuevas animaciones, karaoke ni aceleración CUDA de transcripción. La compilación de Windows conserva los módulos optimizados de CPU del original. Los modelos se descargan desde la aplicación.

FilmCraft se retiró de la rama actual; sus archivos anteriores permanecen en el historial de Git.
