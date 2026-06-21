# HidroMarca GUI

**HidroMarca GUI** es una herramienta local para Windows que permite preparar clips verticales u horizontales reemplazando zonas visuales seleccionadas por el usuario con una marca propia.

La aplicación permite:

- Elegir un video desde una ventana de selección.
- Elegir un audio externo.
- Elegir un logo propio.
- Marcar múltiples zonas superiores e inferiores directamente sobre el frame del video.
- Previsualizar el resultado sin deformar el aspecto del video.
- Exportar un MP4 final con audio sincronizado mediante FFmpeg.

> Esta herramienta está pensada para material propio, demos, clips autorizados o contenido donde tengas permiso para editar marcas, textos o overlays.

## Estado del proyecto

Versión actual: **prototipo funcional local**.

La versión final activa es:

```text
src/hidromarca_gui.py
```

El resto de archivos experimentales usados durante pruebas fueron descartados de la estructura limpia del repositorio.

## Requisitos

- Windows 10/11.
- Python 3.10 o superior.
- FFmpeg instalado y disponible en `PATH`.
- Dependencias Python incluidas en `requirements.txt`.

## Instalación rápida

Clona el repositorio:

```powershell
git clone https://github.com/ElHidrocalido/hidromarca-gui.git
cd hidromarca-gui
```

Instala dependencias:

```powershell
python -m pip install -r requirements.txt
```

Verifica FFmpeg:

```powershell
ffmpeg -version
```

Si FFmpeg no aparece, instala FFmpeg para Windows y agrega su carpeta `bin` al `PATH`.

## Uso

Ejecuta:

```powershell
python .\src\hidromarca_gui.py
```

O en Windows:

```powershell
.\run_hidromarca_gui.bat
```

Dentro de la app:

1. Selecciona el video.
2. Selecciona el audio.
3. Selecciona el logo.
4. Selecciona la ruta de salida.
5. Marca las zonas superiores que quieres reemplazar.
6. Cambia a modo inferior y marca las zonas inferiores.
7. Ajusta texto superior y arroba si hace falta.
8. Exporta el MP4 final.

## Estructura limpia

```text
hidromarca-gui/
├── src/
│   └── hidromarca_gui.py
├── docs/
│   └── USO.md
├── examples/
│   └── .gitkeep
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
└── run_hidromarca_gui.bat
```

## Notas

- El repositorio no debe incluir videos, audios ni renders finales.
- Los archivos `.mp4`, `.mp3`, temporales y resultados están ignorados por `.gitignore`.
- La herramienta no hace inpainting IA todavía; trabaja con zonas seleccionadas por el usuario y composición local con OpenCV/FFmpeg.

## Autor

Proyecto de **EL HIDROCALIDO**.

Repositorio:

```text
https://github.com/ElHidrocalido/hidromarca-gui
```
