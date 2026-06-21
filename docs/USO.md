# Manual de uso

## Objetivo

HidroMarca GUI permite seleccionar zonas visuales de un video y reemplazarlas por texto, logo y arroba propia sin editar coordenadas manualmente.

## Flujo recomendado

1. Ejecuta `run_hidromarca_gui.bat`.
2. Selecciona un archivo de video.
3. Selecciona un archivo de audio.
4. Selecciona un logo.
5. Define el archivo de salida.
6. En **Modo superior**, dibuja una o varias cajas sobre textos superiores que quieras reemplazar.
7. En **Modo inferior**, dibuja una o varias cajas sobre textos o marcas inferiores que quieras reemplazar.
8. Usa **Deshacer zona** si una caja quedó mal.
9. Usa **Limpiar modo** si quieres repetir sólo el modo activo.
10. Presiona **Exportar MP4**.

## Consejos de selección

- Marca sólo la zona que quieres cubrir.
- Usa varias cajas pequeñas en lugar de una caja enorme.
- Si el texto viejo tiene sombra, selecciona también la sombra.
- No cubras zonas importantes del video si no quieres que queden tapadas.

## Salida

La app genera un archivo MP4 final con:

- Video renderizado.
- Audio externo elegido por el usuario.
- Duración ajustada al video.
- Exportación con FFmpeg.

## Limitaciones actuales

- No hace inpainting por IA.
- No reconstruye fondo detrás de textos; tapa zonas seleccionadas.
- La calidad final depende de qué tan precisa sea la selección manual.
