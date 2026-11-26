"""Local still-image conversion. Never replaces a source or an existing output."""
from __future__ import annotations

import base64
import io
import os
import tempfile
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

os.environ.setdefault("OMP_NUM_THREADS", str(min(4, os.cpu_count() or 1)))
import rawpy
from PIL import Image, ImageCms, ImageOps, UnidentifiedImageError
from pillow_heif import register_heif_opener

register_heif_opener()
RAW_EXTENSIONS = frozenset(".cr2 .cr3 .crw .nef .nrw .arw .srf .sr2 .raf .orf .rw2 .pef .dng .raw .rwl .3fr .iiq .kdc .dcr .mos .mrw .x3f .erf .srw".split())
IMAGE_EXTENSIONS = frozenset(".jpg .jpeg .jpe .png .webp .tif .tiff .bmp .gif .avif .heic .heif .ico .jfif".split())
SUPPORTED = RAW_EXTENSIONS | IMAGE_EXTENSIONS
FORMATS = {"jpg": "JPEG", "webp": "WEBP", "png": "PNG", "tiff": "TIFF"}
SRGB = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()


class ConversionError(Exception):
    pass


@dataclass(frozen=True)
class Options:
    format: str = "jpg"
    quality: int = 92
    max_size: int = 0
    lossless: bool = False
    metadata: bool = True
    destination: str = ""

    @classmethod
    def parse(cls, data: dict) -> Options:
        fmt = str(data.get("format", "jpg")).lower()
        quality = int(data.get("quality", 92))
        max_size = int(data.get("max_size", 0))
        destination = str(data.get("destination", "")).strip()
        if fmt not in FORMATS:
            raise ConversionError("Elige JPG, WebP, PNG o TIFF.")
        if not 1 <= quality <= 100 or not 0 <= max_size <= 65535:
            raise ConversionError("La calidad o el tamaño no son válidos.")
        if destination and not Path(destination).is_absolute():
            raise ConversionError("Selecciona una carpeta de destino válida.")
        return cls(fmt, quality, max_size, bool(data.get("lossless", False)), bool(data.get("metadata", True)), destination)


def friendly_error(error: Exception) -> str:
    if isinstance(error, ConversionError):
        return str(error)
    if isinstance(error, PermissionError):
        return "Sin permiso para leer la foto o escribir el resultado. Elige otra carpeta."
    if isinstance(error, FileNotFoundError):
        return "El archivo ya no está disponible. Comprueba la carpeta o la unidad."
    if isinstance(error, (rawpy.LibRawFileUnsupportedError, rawpy.LibRawDataError, UnidentifiedImageError)):
        return "Imagen dañada o formato/cámara no compatible con esta versión."
    if isinstance(error, (Image.DecompressionBombError, Image.DecompressionBombWarning, MemoryError)):
        return "La imagen es demasiado grande para procesarla con seguridad."
    if isinstance(error, OSError) and error.errno == 28:
        return "No queda espacio en la unidad de destino."
    return f"No se pudo convertir: {str(error)[:220]}"


def _normalize(image: Image.Image) -> tuple[Image.Image, list[str]]:
    notes = []
    icc = image.info.get("icc_profile")
    exif = image.info.get("exif")
    if icc:
        try:
            alpha = image.getchannel("A") if "A" in image.getbands() else None
            mode = "CMYK" if image.mode == "CMYK" else "RGB"
            color = image.convert(mode)
            image = ImageCms.profileToProfile(color, ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.ImageCmsProfile(io.BytesIO(SRGB)), outputMode="RGB")
            if alpha is not None:
                image.putalpha(alpha)
        except (OSError, ValueError, ImageCms.PyCMSError):
            notes.append("Perfil de color ilegible; se asumió sRGB.")
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGBA" if "transparency" in image.info or "A" in image.getbands() else "RGB")
    image.info["icc_profile"] = SRGB
    if exif:
        image.info["exif"] = exif
    return image, notes


def read_image(path: Path) -> tuple[Image.Image, list[str]]:
    if path.suffix.lower() in RAW_EXTENSIONS:
        with rawpy.imread(str(path)) as raw:
            pixels = raw.postprocess(use_camera_wb=True, output_color=rawpy.ColorSpace.sRGB, output_bps=8)
        image = Image.fromarray(pixels)
        image.info["icc_profile"] = SRGB
        return image, ["RAW revelado en sRGB; los metadatos de cámara no se copian."]
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with Image.open(path) as source:
            count = getattr(source, "n_frames", 1)
            source.seek(0)
            image = ImageOps.exif_transpose(source)
            image.load()
            image = image.copy()
    image, notes = _normalize(image)
    if count > 1:
        notes.append("Se convirtió únicamente el primer fotograma o página.")
    return image, notes


def thumbnail(path: Path, size: int = 1100) -> dict:
    """Embedded RAW preview when available; full development is reserved for export."""
    notes = []
    if path.suffix.lower() in RAW_EXTENSIONS:
        with rawpy.imread(str(path)) as raw:
            width, height = raw.sizes.width, raw.sizes.height
            if raw.sizes.flip in (5, 6):
                width, height = height, width
            try:
                thumb = raw.extract_thumb()
                if thumb.format == rawpy.ThumbFormat.JPEG:
                    with Image.open(io.BytesIO(thumb.data)) as embedded:
                        embedded.load()
                        image = ImageOps.exif_transpose(embedded).copy()
                else:
                    image = Image.fromarray(thumb.data)
                # LibRaw's embedded preview may have no EXIF orientation.
                if (width > height) != (image.width > image.height) and width != height:
                    image = image.transpose(Image.Transpose.ROTATE_270 if raw.sizes.flip == 6 else Image.Transpose.ROTATE_90)
            except (rawpy.LibRawNoThumbnailError, rawpy.LibRawUnsupportedThumbnailError):
                image = Image.fromarray(raw.postprocess(half_size=True, use_camera_wb=True, output_bps=8))
            notes.append("Vista previa RAW; el resultado se revela a resolución completa.")
    else:
        image, notes = read_image(path)
        width, height = image.size
    image.thumbnail((size, size), Image.Resampling.LANCZOS)
    if image.mode != "RGB":
        background = Image.new("RGB", image.size, "#242424")
        if "A" in image.getbands():
            background.paste(image, mask=image.getchannel("A"))
        else:
            background.paste(image.convert("RGB"))
        image = background
    output = io.BytesIO()
    image.save(output, "JPEG", quality=83)
    return {"image": "data:image/jpeg;base64," + base64.b64encode(output.getvalue()).decode("ascii"), "width": width, "height": height, "note": " ".join(notes)}


def convert(path: Path, options: Options, cancelled: Callable[[], bool] = lambda: False) -> dict:
    if path.suffix.lower() not in SUPPORTED:
        raise ConversionError("El tipo de archivo no está admitido.")
    image, notes = read_image(path)
    try:
        if options.max_size:
            image.thumbnail((options.max_size, options.max_size), Image.Resampling.LANCZOS)
        if options.format == "jpg" and image.mode == "RGBA":
            background = Image.new("RGB", image.size, "white")
            background.paste(image, mask=image.getchannel("A"))
            background.info = image.info.copy()
            image = background
            notes.append("Transparencia sustituida por fondo blanco para JPG.")
        exif = image.getexif() if options.metadata else Image.Exif()
        for tag in (256, 257, 274, 40962, 40963, 513, 514):
            if tag in exif:
                del exif[tag]
        if options.format == "webp" and max(image.size) > 16383:
            raise ConversionError("WebP admite hasta 16 383 px por lado. Activa Reducir tamaño.")
        args = {"icc_profile": SRGB}
        if exif:
            args["exif"] = exif.tobytes()
        if options.format == "jpg":
            args.update(quality=options.quality, subsampling=0 if options.quality >= 90 else 2, optimize=True)
        elif options.format == "webp":
            args.update(quality=options.quality, lossless=options.lossless, method=4)
        elif options.format == "png":
            args.update(compress_level=6)
        elif options.format == "tiff":
            args.update(compression="tiff_lzw")
        folder = Path(options.destination) if options.destination else path.parent / "Revela"
        folder.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".revela-", suffix=".tmp", dir=folder)
        os.close(fd)
        temporary = Path(temporary)
        reserved = None
        try:
            image.save(temporary, format=FORMATS[options.format], **args)
            if cancelled():
                return {"cancelled": True}
            # Exclusive reservation prevents collisions even between simultaneous app instances.
            for index in range(100000):
                suffix = "" if index == 0 else f" ({index})"
                target = folder / f"{path.stem}{suffix}.{options.format}"
                try:
                    with target.open("xb"):
                        pass
                    reserved = target
                    break
                except FileExistsError:
                    continue
            if reserved is None:
                raise ConversionError("Hay demasiados archivos con el mismo nombre en el destino.")
            os.replace(temporary, reserved)
            result = {"output": str(reserved), "bytes": reserved.stat().st_size, "width": image.width, "height": image.height, "note": " ".join(notes)}
            reserved = None
            return result
        finally:
            temporary.unlink(missing_ok=True)
            if reserved is not None:
                reserved.unlink(missing_ok=True)
    finally:
        image.close()
