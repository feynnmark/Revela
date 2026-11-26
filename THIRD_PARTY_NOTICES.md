# Dependencias y procedencia

Revela utiliza bibliotecas de terceros sin modificarlas. Los avisos completos se distribuyen en `_internal/licenses/` y en `_internal/ui/assets/Inter-LICENSE.txt`.

| Componente | Versión | Licencia / fuente |
| --- | --- | --- |
| Python | 3.14 | PSF, https://www.python.org/ |
| rawpy | 0.28.0 | MIT, https://github.com/letmaik/rawpy |
| LibRaw | 0.22.2 | LGPL 2.1, avisos del paquete rawpy en LICENSE.LibRaw; https://www.libraw.org/ |
| Pillow | 12.3.0 | HPND y avisos de codecs incluidos; https://github.com/python-pillow/Pillow |
| pillow-heif | 1.8.1 | BSD y licencias de libheif/codecs en LICENSES_bundled.txt; https://github.com/bigcat88/pillow_heif |
| NumPy | 2.5.4 | BSD y avisos incluidos; https://numpy.org/ |
| pywebview | 6.2.1 | BSD 3-Clause, https://github.com/r0x0r/pywebview |
| pythonnet | 3.2.1 | MIT, https://github.com/pythonnet/pythonnet |
| clr-loader | 0.3.1 | MIT, https://github.com/pythonnet/clr-loader |
| Inter | variable font | SIL Open Font License 1.1, https://github.com/rsms/inter |
| Microsoft WebView2 SDK binaries | Incluidos por pywebview | Avisos de Microsoft en la distribución del SDK; WebView2 Runtime instalado por separado en Windows. https://learn.microsoft.com/microsoft-edge/webview2/ |
| PyInstaller | 6.22.3 | GPL con excepción de bootloader que permite distribuir aplicaciones empaquetadas. No cambia las licencias de las dependencias. https://pyinstaller.org/ |

También se conservan los avisos de las dependencias transitivas en la carpeta de licencias. Las bibliotecas empaquetadas permanecen en archivos separados dentro de `_internal`; no se aplica ofuscación ni restricción de sustitución de bibliotecas. Fuentes y construcción de rawpy: https://github.com/letmaik/rawpy/tree/v0.28.0. Fuentes upstream de LibRaw: https://github.com/LibRaw/LibRaw/tree/0.22.2. Pillow-heif incluye su lista de dependencias y licencias de codecs.

El icono y marca R son geometría original de este proyecto, dibujada por `tools/make_icon.py` y `ui/assets/mark.svg`. La tipografía se distribuye desde su repositorio original con licencia. No se utilizan imágenes generadas ni fotografías de relleno en la app.

Las fotografías de prueba y los resultados no se distribuyen. Las pruebas opcionales admiten muestras de cualquier formato RAW compatible. Pueden obtenerse archivos de rawpy (https://github.com/letmaik/rawpy/tree/main/test) y raw.pixls.us (https://raw.pixls.us/), sujetos a la licencia individual de cada muestra.
