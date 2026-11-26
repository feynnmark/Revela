# Pruebas

## Motor y cola

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Las pruebas crean sus propias imágenes en carpetas temporales. Comprueban los formatos de salida, proporciones, transparencia, perfiles de color, EXIF, orientación, nombres duplicados, originales intactos, cancelación y continuidad de una tanda ante archivos dañados.

## Archivos RAW

Las pruebas opcionales aceptan cualquier formato de `RAW_EXTENSIONS`. Define `REVELA_RAW_FIXTURES` con una carpeta de muestras o colócalas en `.local/fixtures`. Las fotografías no forman parte del repositorio ni de la distribución.

```powershell
$env:REVELA_RAW_FIXTURES = Join-Path $env:TEMP 'Revela-raw-fixtures'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Cada muestra se abre para vista previa y se convierte a JPG y WebP; su SHA-256 debe conservarse. Se han validado muestras de CR2, CR3 y NEF. Estas verificaciones son ejemplos de cobertura, no una lista exclusiva de dispositivos compatibles.

Pueden obtenerse muestras de [rawpy](https://github.com/letmaik/rawpy/tree/main/test) o [raw.pixls.us](https://raw.pixls.us/). Comprueba la licencia de cada archivo antes de redistribuirlo.

## Ejecutable empaquetado

```powershell
$testRoot = Join-Path $env:TEMP 'Revela-package-test'
.\dist\Revela\Revela.exe --self-test $testRoot
.\dist\Revela\Revela.exe --smoke-test (Join-Path $testRoot 'smoke.json')
```

El primer comando verifica los codecs incluidos creando y reabriendo JPG, WebP, PNG y TIFF. También admite rutas de imágenes como argumentos adicionales. El segundo abre la ventana con WebView2 y comprueba la interfaz, el puente con Python y los recursos incluidos.

## Revisión antes de publicar

```powershell
.\.venv\Scripts\python.exe tools\audit_public.py --source
.\.venv\Scripts\python.exe tools\audit_public.py --package dist\Revela
```

La revisión examina archivos que Git va a publicar y el paquete, incluidos sus archivos comprimidos y los nombres de origen del código empaquetado. Rechaza claves reconocibles, rutas de perfiles de usuario, cachés, registros y archivos locales. Es una comprobación adicional a la revisión manual y al análisis de secretos con Gitleaks.
