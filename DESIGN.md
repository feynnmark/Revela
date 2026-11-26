---
name: Revela
description: Conversor local de imágenes para Windows, oscuro y sobrio.
colors:
  ground: "#0e0e0e"
  surface: "#171717"
  raised: "#242424"
  control: "#323232"
  rule: "#2a2a2a"
  text: "#f2f1ee"
  muted: "#b4b4b4"
  faint: "#969696"
  accent: "#d4ae82"
  positive: "#b2cf9c"
  negative: "#efa09b"
typography:
  brand:
    fontFamily: "Inter, 'Segoe UI', sans-serif"
    fontSize: "25px"
    fontWeight: 550
    letterSpacing: "-0.05em"
  headline:
    fontFamily: "Inter, 'Segoe UI', sans-serif"
    fontSize: "23px"
    fontWeight: 500
    letterSpacing: "-0.035em"
  empty-title:
    fontFamily: "Inter, 'Segoe UI', sans-serif"
    fontSize: "22px"
    fontWeight: 450
    letterSpacing: "-0.035em"
  title:
    fontFamily: "Inter, 'Segoe UI', sans-serif"
    fontSize: "16px"
    fontWeight: 500
    letterSpacing: "-0.02em"
  body:
    fontFamily: "Inter, 'Segoe UI', sans-serif"
    fontSize: "13px"
    fontWeight: 400
  label:
    fontFamily: "Inter, 'Segoe UI', sans-serif"
    fontSize: "12px"
    fontWeight: 500
  detail:
    fontFamily: "Inter, 'Segoe UI', sans-serif"
    fontSize: "11px"
    fontWeight: 400
rounded:
  checkbox: "4px"
  field: "5px"
  segment: "6px"
  control: "7px"
  button: "8px"
  picker: "9px"
  surface: "12px"
  dialog: "14px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "20px"
  column: "26px"
  frame: "30px"
components:
  button-primary:
    backgroundColor: "{colors.text}"
    textColor: "{colors.ground}"
    typography: "{typography.label}"
    rounded: "{rounded.button}"
    padding: "0 15px"
  button-secondary:
    backgroundColor: "{colors.raised}"
    textColor: "{colors.text}"
    typography: "{typography.label}"
    rounded: "{rounded.button}"
    padding: "0 15px"
  button-secondary-hover:
    backgroundColor: "{colors.control}"
    textColor: "{colors.text}"
  button-stop:
    backgroundColor: "{colors.raised}"
    textColor: "{colors.text}"
    rounded: "{rounded.button}"
    padding: "0 15px"
  button-icon:
    textColor: "{colors.faint}"
    rounded: "{rounded.control}"
    width: "30px"
    height: "30px"
  format-segment:
    textColor: "{colors.muted}"
    rounded: "{rounded.segment}"
    padding: "10px 3px"
  format-segment-selected:
    backgroundColor: "{colors.control}"
    textColor: "{colors.text}"
    rounded: "{rounded.segment}"
    padding: "10px 3px"
  number-field:
    backgroundColor: "{colors.raised}"
    textColor: "{colors.text}"
    rounded: "{rounded.field}"
    padding: "7px"
    width: "85px"
  work-surface:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.surface}"
---

# Design System: Revela

## Overview

**Creative North Star: "Hoja de contacto fotográfica"**

Esta frase describe la implementación actual; no es una promesa de marca confirmada. La preferencia confirmada es una interfaz en español, oscura y sobria. Una superficie gráfica silenciosa deja el protagonismo a las fotografías y a las decisiones de exportación.

El diseño es compacto, plano y utilitario: cola y vista previa a la izquierda, ajustes y conversión a la derecha. Usa una sola familia tipográfica y símbolos de trazo coherentes. La marca, la ilustración vacía y los iconos son geometría original; el arte raster de distribución se genera con `tools/make_icon.py`. Las fotografías proceden de archivos del usuario o de fixtures locales de verificación, sin fotografías decorativas.

**Key Characteristics:**
- Oscuro y sobrio, con capas tonales de gris.
- Tipografía Inter local y jerarquía compacta.
- Fotografías reales como contenido de trabajo.
- Acción de conversión siempre accesible junto a ajustes desplazables.

## Colors

La paleta combina negros neutros, texto marfil y ámbar contenido. Los valores normativos están en el frontmatter y corresponden a las variables de `ui/style.css`.

### Primary

- **Ámbar fotográfico** (`accent`): punto de marca, archivos RAW, archivo en proceso, progreso y foco de teclado. La acción principal usa marfil, no ámbar.

### Neutral

- **Negro base** (`ground`): fondo general y texto de botones claros.
- **Grafito de trabajo** (`surface`): superficie principal y base del selector de formato.
- **Grafito elevado** (`raised`): botones secundarios, campos y pista de progreso.
- **Grafito de control** (`control`): segmento seleccionado, hover secundario y bordes de campos.
- **Divisor** (`rule`): separaciones estructurales discretas.
- **Marfil** (`text`): texto principal, botones primarios y controles marcados.
- **Gris secundario** (`muted`): metadatos y acciones auxiliares.
- **Gris de detalle** (`faint`): explicaciones, notas, estados pendientes e iconos auxiliares.

Los colores semánticos **verde de éxito** (`positive`) y **coral de error** (`negative`) acompañan estados escritos y sus iconos; no forman acentos decorativos adicionales.

## Typography

Inter variable se distribuye localmente en `ui/assets/Inter.woff2`, con Segoe UI y sans-serif como alternativas. No hay fuente remota ni familia monoespaciada. Los porcentajes, dimensiones y contadores usan cifras tabulares.

- **Brand:** nombre Revela; el punto final lleva el acento.
- **Headline:** título del área de imágenes; se reduce a 21 px en la variante estrecha.
- **Empty title:** invitación del estado vacío; se reduce a 20 px en la variante estrecha.
- **Title:** encabezados secundarios; el título de exportación usa una variante de 15 px y el diálogo de ayuda, 21 px.
- **Body:** texto base; los párrafos usan interlineado 1.6, con variantes mayores para ayuda y estado vacío.
- **Label:** botones y etiquetas de ajustes.
- **Detail:** cola, notas, pie, formatos y acciones auxiliares.

## Layout

Ventana Windows con WebView2: tamaño exterior inicial 1220 × 830 px y mínimo exterior 960 × 690 px. El contenido interior es menor por la barra de título y los bordes nativos; los media queries responden al viewport interior, no al tamaño exterior. No se implementa una composición móvil.

La cabecera mide 70 px y el pie 34 px. El cuerpo usa dos columnas: trabajo flexible y ajustes de 306 px, con separación de 26 px y margen horizontal de 30 px. Hasta 1080 px de ancho interior, los ajustes pasan a 280 px, los márgenes a 22 px y la separación a 20 px; las acciones superiores pueden saltar de línea y se ocultan textos auxiliares. Hasta 760 px de alto interior se compactan cabecera, márgenes y vista previa. Desde 900 px de alto crece el espacio de la zona de trabajo.

La página no se desplaza. En ajustes, solo la región superior de controles tiene scroll; conserva un gutter estable y una barra visible de 6 px. Cuando hay contenido oculto aparece debajo «Ver más ajustes», que cambia a «Volver arriba» al llegar al fondo. La acción de conversión está fuera de esa región, fija al pie de la columna mediante flex y sin contracción. La cola tiene su propio scroll y ocupa aproximadamente el 42 % de la superficie; en ventanas altas usa el 39 %. La vista previa ocupa el espacio restante y muestra la fotografía completa con `object-fit: contain`.

## Elevation & Depth

No hay sombras CSS. La profundidad procede de superficies tonales, divisores finos y el cambio de fondo de los controles. El diálogo modal añade un velo negro translúcido; la notificación usa un borde algo más visible. El foco no se comunica con sombra: usa un contorno ámbar de 2 px.

## Shapes

Esquinas suavizadas y moderadas, según la escala del frontmatter: superficies amplias más redondeadas que los controles pequeños. Los campos y varios controles usan bordes de 1 px. Los puntos de estado y el pulgar del deslizador son circulares. Los iconos de interfaz son SVG de trazo redondeado, normalmente de 18 px, con grosor 1.65.

## Components

- **Botones:** altura mínima habitual de 38 px, texto de 12 px y separación de 8 px entre icono y etiqueta. El primario pasa de marfil a blanco al hacer hover; el secundario pasa de grafito elevado a grafito de control. Los botones deshabilitados tienen opacidad 0.38 y cursor por defecto. El botón de conversión tiene altura mínima de 43 px y ancho completo; durante la tanda se convierte en acción de detener con fondo oscuro y borde visible.
- **Acciones auxiliares:** botones de icono discretos que aclaran texto y fondo al hacer hover; enlaces de acción que subrayan su texto al hacer hover. «Ver más ajustes» permite recorrer la región desplazable y pasa a «Volver arriba» con la flecha invertida; el desplazamiento respeta movimiento reducido.
- **Formatos:** grupo real de radios de cuatro segmentos. El seleccionado tiene fondo de control y texto marfil; el foco rodea el segmento y un radio deshabilitado queda a media opacidad. No es navegación entre pantallas.
- **Campos:** selector nativo oscuro de 36 px de alto; campo numérico compacto para tamaño personalizado. Checkbox de 16 px, claro al marcarse. Calidad usa deslizador de 4 px con pulgar circular de 13 px. WebP muestra una opción sin pérdida; la calidad se oculta cuando no aplica.
- **Foco y movimiento:** contorno visible ámbar de 2 px, normalmente separado 4 px del control. Los botones cambian fondo, color y opacidad en 160 ms; el progreso cambia ancho en 300 ms con la curva del sidecar. Se eliminan transiciones y animaciones con movimiento reducido.
- **Superficie y cola:** la superficie contiene estado vacío o vista previa y archivos. Filas de al menos 53 px con nombre, metadatos, estado escrito y acción de quitar. El seleccionado y el hover cambian el gris de fondo; la selección expone `aria-pressed`. Los errores permanecen junto al archivo y se pueden reintentar.
- **Feedback:** barra ámbar fina con contador, estado global anunciado, notificación textual y diálogo de ayuda. Éxito y error siempre incluyen texto; éxito y error de archivo también incluyen icono. Los nombres largos y rutas se truncan en los espacios limitados.

## Do's and Don'ts

### Do:

- **Do** mantener la apariencia oscura y sobria y la interfaz en español.
- **Do** conservar visibles la acción de conversión y el acceso por teclado al reducir la ventana.
- **Do** usar fotografías de entrada reales, Inter local e iconos originales de trazo coherente.
- **Do** acompañar los colores de estado con texto y conservar el foco visible.

### Don't:

- **Don't** introducir sombras decorativas o acentos saturados ajenos a la paleta actual.
- **Don't** ocultar la conversión dentro del scroll de ajustes.
- **Don't** recortar la fotografía para rellenar la vista previa.
- **Don't** tratar las dimensiones exteriores de Windows como dimensiones interiores del contenido.
