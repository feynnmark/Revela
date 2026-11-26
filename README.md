# Revela

Conversor de imágenes para Windows. Convierte fotografías RAW y formatos comunes a JPG, WebP, PNG o TIFF, de forma individual o por tandas. El procesamiento se realiza en tu equipo y conserva los originales.

## Descargar e instalar

1. Abre [la última versión](https://github.com/feynnmark/Revela/releases/latest).
2. En **Assets**, descarga `Revela-<versión>-Windows-x64.zip`. Los archivos **Source code** contienen el código fuente, no la aplicación lista para usar.
3. Haz clic derecho en el ZIP y elige **Extraer todo**. Conserva juntos todos los archivos extraídos.
4. Abre la carpeta **Revela** y ejecuta **Install.cmd**. Se crearán los accesos en el escritorio y el menú Inicio. No requiere permisos de administrador.

Para usarla sin instalar, abre **Revela.exe** desde la carpeta extraída. La carpeta `_internal` debe permanecer junto al ejecutable. No necesitas instalar Python.

### Requisitos

- Windows 10 u 11 de 64 bits, en un equipo Intel o AMD.
- [Microsoft Edge WebView2 Runtime](https://developer.microsoft.com/microsoft-edge/webview2/#download-section) y [.NET Framework 4.8 o posterior](https://dotnet.microsoft.com/download/dotnet-framework/net48), normalmente disponibles en Windows actualizado.

La distribución actual es para Windows x64. No incluye versiones nativas para macOS, Linux o Windows ARM.

## Convertir imágenes

1. Arrastra fotos o carpetas a la ventana, o usa **Añadir imágenes** y **Carpeta**.
2. Elige JPG, WebP, PNG o TIFF. Ajusta la calidad y, si lo necesitas, el tamaño máximo.
3. Selecciona dónde guardar. Por defecto se crea una carpeta **Revela** junto a cada original.
4. Pulsa **Convertir**. Al terminar, usa **Abrir resultados**.

Las carpetas se recorren con sus subcarpetas. Los archivos existentes reciben un número para evitar sobrescrituras. Puedes detener una tanda, reintentar los archivos con error y guardar un informe CSV. **Ctrl + O** añade imágenes; **Ctrl + Enter** inicia la conversión.

## Compatibilidad

Trabaja con archivos de cámaras y teléfonos de distintas marcas. No requiere conectar el dispositivo ni instalar sus controladores.

| Entrada | Formatos |
| --- | --- |
| RAW | CR2, CR3, NEF, NRW, ARW, RAF, ORF, RW2, PEF, DNG y otros admitidos por LibRaw |
| Imágenes | JPG, PNG, WebP, TIFF, BMP, GIF, AVIF, HEIC, HEIF e ICO |
| Salida | JPG, WebP con o sin pérdida, PNG y TIFF con compresión LZW |

La compatibilidad RAW depende del formato y del modelo de cámara admitido por la versión de [LibRaw](https://www.libraw.org/supported-cameras) incluida. Las muestras de prueba no limitan la app a esas cámaras; tampoco garantizan compatibilidad con todos los modelos.

Todas las salidas tienen 8 bits por canal y color sRGB, incluido TIFF. En animaciones o archivos con varias páginas se convierte únicamente la primera imagen. JPG sustituye la transparencia por blanco. La reducción conserva las proporciones y nunca amplía.

## Privacidad

Sin cuentas, telemetría ni subida de fotografías. La opción **Conservar metadatos** mantiene el EXIF disponible de imágenes comunes, que puede incluir ubicación GPS; desactívala para quitarlo. Los RAW se exportan sin EXIF de cámara.

Los ajustes y registros se guardan localmente en `%LOCALAPPDATA%\Revela`. Los registros y los informes CSV pueden incluir nombres o rutas de archivos: revísalos antes de compartirlos.

## Actualizar o desinstalar

Para actualizar, cierra Revela y ejecuta **Install.cmd** del paquete nuevo. Para quitarla, abre **Configuración > Aplicaciones > Aplicaciones instaladas > Revela**. Tus fotos, resultados y preferencias se conservan.

Si la app no abre, comprueba los requisitos e instala WebView2 desde el enlace oficial. Si falta un archivo del paquete, vuelve a extraer el ZIP completo. Si una imagen falla, la tanda continúa y la fila muestra el motivo.

## Compilar desde el código

Requiere Windows x64, Git y Python 3.14 x64.

```powershell
git clone https://github.com/feynnmark/Revela.git
cd Revela
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\build.ps1 -Test -Package
```

El paquete se genera en `dist`. Para ejecutar el código directamente:

```powershell
.\.venv\Scripts\python.exe app.py
```

Consulta [las pruebas](TESTING.md), [el diseño](DESIGN.md) y [los avisos de dependencias](THIRD_PARTY_NOTICES.md). El código de Revela se distribuye bajo [licencia MIT](LICENSE); las dependencias conservan sus propias licencias.
