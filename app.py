from __future__ import annotations

import argparse
import csv
import ctypes
import json
import logging
import os
import sys
import threading
import time
import uuid
from collections import OrderedDict
from pathlib import Path

from engine import Options, SUPPORTED, RAW_EXTENSIONS, convert, friendly_error, thumbnail

ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
DATA = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Revela"


class Api:
    def __init__(self, settings_path=None):
        self._window = None
        self._lock = threading.RLock()
        self._files = []
        self._revision = 0
        self._busy = False
        self._scanning = False
        self._cancel = threading.Event()
        self._cache = OrderedDict()
        self._preview_lock = threading.Lock()
        self._worker = None
        self._settings_path = Path(settings_path) if settings_path else DATA / "settings.json"
        self._settings = dict(format="jpg", quality=92, max_size=0, lossless=False, metadata=True, destination="")
        self._message = "Todo listo para tu próxima tanda."
        self._batch = dict(total=0, completed=0, errors=0, cancelled=False, elapsed=0)
        try:
            self._settings.update(json.loads(self._settings_path.read_text(encoding="utf-8")))
            self._settings = vars(Options.parse(self._settings))
        except (OSError, ValueError, TypeError):
            pass

    def get_state(self, revision=-1):
        with self._lock:
            if revision == self._revision:
                return None
            return dict(revision=self._revision, version=VERSION, files=[dict(f) for f in self._files], busy=self._busy, scanning=self._scanning, cancelling=self._cancel.is_set() and self._busy, settings=dict(self._settings), message=self._message, batch=dict(self._batch))

    def _touch(self):
        self._revision += 1

    def choose_files(self):
        import webview
        paths = self._window.create_file_dialog(webview.FileDialog.OPEN, allow_multiple=True, file_types=("Imágenes (" + ";".join("*" + ext for ext in sorted(SUPPORTED)) + ")", "Todos los archivos (*.*)"))
        return self.add_paths(list(paths or []))

    def choose_folder(self):
        import webview
        paths = self._window.create_file_dialog(webview.FileDialog.FOLDER)
        return self.add_paths(list(paths or []))

    def choose_destination(self):
        import webview
        paths = self._window.create_file_dialog(webview.FileDialog.FOLDER, directory=self._settings.get("destination") or "")
        if paths:
            return self.update_settings({"destination": paths[0]})
        return {"ok": True}

    def add_paths(self, paths):
        with self._lock:
            if self._busy or self._scanning:
                return {"error": "Espera a que termine la tarea actual."}
            if not paths:
                return {"ok": True}
            self._scanning = True
            self._message = "Buscando imágenes…"
            self._touch()
        threading.Thread(target=self._scan, args=(paths,), daemon=True).start()
        return {"ok": True}

    def _scan(self, paths):
        added, ignored, unreadable = 0, 0, 0
        with self._lock:
            known = {os.path.normcase(f["path"]) for f in self._files}
        def candidates():
            nonlocal unreadable
            for entry in paths:
                path = Path(str(entry)).resolve()
                if path.is_dir():
                    def walk_error(_):
                        nonlocal unreadable
                        unreadable += 1
                    for directory, directories, files in os.walk(path, onerror=walk_error, followlinks=False):
                        directories[:] = sorted(d for d in directories if d.lower() != "revela" and not d.startswith(".") and not (Path(directory) / d).is_symlink())
                        for name in sorted(files):
                            yield Path(directory) / name
                else:
                    yield path
        try:
            for path in candidates():
                if path.suffix.lower() not in SUPPORTED:
                    ignored += 1
                    continue
                key = os.path.normcase(str(path))
                if key in known:
                    continue
                try:
                    size = path.stat().st_size
                    if not path.is_file():
                        continue
                except OSError:
                    unreadable += 1
                    continue
                with self._lock:
                    if len(self._files) >= 10000:
                        self._message = "Límite de 10 000 imágenes por tanda."
                        break
                    self._files.append(dict(id=uuid.uuid4().hex, path=str(path), name=path.name, extension=path.suffix[1:].upper(), raw=path.suffix.lower() in RAW_EXTENSIONS, size=size, state="pending", error="", output="", note=""))
                    self._touch()
                known.add(key)
                added += 1
            else:
                with self._lock:
                    self._message = f"{added} {'imagen añadida' if added == 1 else 'imágenes añadidas'}."
                    if ignored:
                        self._message += f" {ignored} archivo(s) de otros tipos omitidos."
                    if unreadable:
                        self._message += f" {unreadable} ubicación(es) sin acceso."
        except Exception as error:
            logging.exception("Import failed")
            with self._lock:
                self._message = friendly_error(error)
        finally:
            with self._lock:
                self._scanning = False
                self._touch()

    def get_preview(self, identifier):
        with self._lock:
            item = next((dict(f) for f in self._files if f["id"] == identifier), None)
        if not item:
            return {"error": "La imagen ya no está en la tanda."}
        with self._preview_lock:
            if identifier in self._cache:
                self._cache.move_to_end(identifier)
                return self._cache[identifier]
            try:
                result = thumbnail(Path(item["path"]))
            except Exception as error:
                result = {"error": friendly_error(error)}
            self._cache[identifier] = result
            while len(self._cache) > 8:
                self._cache.popitem(last=False)
            return result

    def update_settings(self, changes):
        with self._lock:
            if self._busy:
                return {"error": "Espera a que termine la conversión."}
            try:
                updated = dict(self._settings)
                updated.update({k: v for k, v in changes.items() if k in self._settings})
                self._settings = vars(Options.parse(updated))
                self._settings_path.parent.mkdir(parents=True, exist_ok=True)
                temp = self._settings_path.with_suffix(".tmp")
                temp.write_text(json.dumps(self._settings, ensure_ascii=False, indent=2), encoding="utf-8")
                temp.replace(self._settings_path)
                self._touch()
                return {"ok": True}
            except Exception as error:
                return {"error": friendly_error(error)}

    def remove_file(self, identifier):
        with self._lock:
            if self._busy or self._scanning:
                return {"error": "Espera a que termine la tarea actual."}
            self._files = [f for f in self._files if f["id"] != identifier]
            self._touch()
        return {"ok": True}

    def clear(self):
        with self._lock:
            if self._busy or self._scanning:
                return {"error": "Espera a que termine la tarea actual."}
            self._files.clear()
            self._message = "Todo listo para tu próxima tanda."
            self._batch = dict(total=0, completed=0, errors=0, cancelled=False, elapsed=0)
            self._touch()
        with self._preview_lock:
            self._cache.clear()
        return {"ok": True}

    def start_batch(self, again=False):
        with self._lock:
            if self._busy or self._scanning:
                return {"error": "Ya hay una tarea en curso."}
            selected = [f for f in self._files if again or f["state"] != "done"]
            if not selected:
                return {"error": "Añade imágenes a la tanda."}
            options = Options.parse(self._settings)
            self._cancel.clear()
            self._busy = True
            self._batch = dict(total=len(selected), completed=0, errors=0, cancelled=False, elapsed=0)
            for item in selected:
                item.update(state="pending", error="", note="", output="")
            self._touch()
        self._worker = threading.Thread(target=self._run, args=(selected, options), daemon=True)
        self._worker.start()
        return {"ok": True}

    def _run(self, selected, options):
        started = time.monotonic()
        try:
            for item in selected:
                if self._cancel.is_set():
                    break
                with self._lock:
                    item["state"] = "working"
                    self._message = f"Convirtiendo {item['name']}…"
                    self._touch()
                try:
                    result = convert(Path(item["path"]), options, self._cancel.is_set)
                    with self._lock:
                        if result.get("cancelled"):
                            item["state"] = "pending"
                            break
                        item.update(state="done", output=result["output"], output_size=result["bytes"], width=result["width"], height=result["height"], note=result["note"])
                        self._batch["completed"] += 1
                except Exception as error:
                    logging.exception("Conversion failed for %s", item["name"])
                    with self._lock:
                        item.update(state="error", error=friendly_error(error))
                        self._batch["errors"] += 1
                with self._lock:
                    self._batch["elapsed"] = round(time.monotonic() - started, 1)
                    self._touch()
        finally:
            with self._lock:
                self._busy = False
                self._batch["cancelled"] = self._cancel.is_set()
                self._batch["elapsed"] = round(time.monotonic() - started, 1)
                count, errors = self._batch["completed"], self._batch["errors"]
                self._message = ("Tanda detenida." if self._cancel.is_set() else "Tanda terminada.") + f" {count} convertida(s)" + (f" · {errors} con error." if errors else ".")
                self._touch()

    def cancel_batch(self):
        with self._lock:
            if self._busy:
                self._cancel.set()
                self._message = "Deteniendo… El archivo actual puede tardar unos segundos."
                self._touch()
        return {"ok": True}

    def open_output(self, identifier=""):
        with self._lock:
            item = next((f for f in self._files if f["id"] == identifier and f["output"]), None)
            outputs = [f["output"] for f in self._files if f["output"]]
            path = Path(item["output"]).parent if item else Path(outputs[-1]).parent if outputs else Path(self._settings["destination"]) if self._settings["destination"] else None
        if path and path.is_dir():
            os.startfile(str(path))
            return {"ok": True}
        return {"error": "Todavía no hay una carpeta de salida. Convierte una imagen primero."}

    def export_report(self):
        import webview
        path = self._window.create_file_dialog(webview.FileDialog.SAVE, save_filename="Revela-informe.csv", file_types=("Informe CSV (*.csv)",))
        if not path:
            return {"ok": True}
        target = Path(path if isinstance(path, str) else path[0])
        with self._lock:
            rows = [dict(f) for f in self._files]
        if any(os.path.normcase(str(target.resolve())) in (os.path.normcase(f["path"]), os.path.normcase(f.get("output", ""))) for f in rows):
            return {"error": "El informe necesita un nombre distinto al de las imágenes."}
        try:
            with target.open("w", newline="", encoding="utf-8-sig") as stream:
                writer = csv.writer(stream)
                writer.writerow(["Origen", "Estado", "Resultado", "Error", "Nota"])
                for f in rows:
                    # Prevent spreadsheet formula interpretation of untrusted filenames.
                    writer.writerow([("'" + str(v)) if str(v).lstrip().startswith(("=", "+", "-", "@")) else v for v in (f["path"], f["state"], f["output"], f["error"], f["note"])])
            return {"ok": True, "message": "Informe guardado."}
        except Exception as error:
            return {"error": friendly_error(error)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*")
    parser.add_argument("--smoke-test", metavar="REPORT")
    parser.add_argument("--self-test", metavar="DIRECTORY")
    args = parser.parse_args()
    DATA.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=DATA / "revela.log", level=logging.WARNING, format="%(asctime)s %(levelname)s %(message)s")
    if args.self_test:
        from PIL import Image
        testdir = Path(args.self_test)
        testdir.mkdir(parents=True, exist_ok=True)
        original = testdir / "prueba.png"
        Image.new("RGBA", (160, 90), (100, 150, 80, 120)).save(original)
        reports = [convert(original, Options(format=fmt, destination=str(testdir / "resultados"))) for fmt in ("jpg", "webp", "png", "tiff")]
        for source in args.files:
            thumbnail(Path(source))
            reports.extend(convert(Path(source), Options(format=fmt, destination=str(testdir / "resultados"))) for fmt in ("jpg", "webp"))
        for result in reports:
            with Image.open(result["output"]) as verified:
                verified.verify()
        (testdir / "resultado.json").write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")
        return
    import webview
    api = Api()
    window = webview.create_window("Revela", str(ROOT / "ui" / "index.html"), js_api=api, width=1220, height=830, min_size=(960, 690), background_color="#0e0e0e", text_select=True)
    api._window = window
    def on_closing():
        if api._busy:
            if not window.create_confirmation_dialog("Conversión en curso", "¿Detener la tanda y cerrar Revela? Se conservarán los resultados ya terminados."):
                return False
            api._cancel.set()
            window.hide()
            def finish_then_close():
                if api._worker:
                    api._worker.join()
                window.destroy()
            threading.Thread(target=finish_then_close, daemon=True).start()
            return False
        return True
    window.events.closing += on_closing
    def bind_drop():
        from webview.dom import DOMEventHandler
        def drop(event):
            paths = [f.get("pywebviewFullPath") for f in event.get("dataTransfer", {}).get("files", [])]
            api.add_paths([p for p in paths if p])
        window.dom.document.events.drop += DOMEventHandler(drop, prevent_default=True)
    window.events.loaded += bind_drop
    def started():
        if args.files:
            api.add_paths(args.files)
        if args.smoke_test:
            try:
                for _ in range(100):
                    ready = window.evaluate_js("Boolean(window.revelaReady)")
                    if ready:
                        break
                    time.sleep(.15)
                time.sleep(1)
                result = window.evaluate_js("({title:document.title, ready:!!window.revelaReady, buttons:document.querySelectorAll('button').length, bodyWidth:document.body.scrollWidth, width:innerWidth, bridge:!!window.pywebview.api.start_batch, logo:document.querySelector('.brand img').naturalWidth>0, font:document.fonts.check('12px Inter'), height:innerHeight, destinationVisible:document.getElementById('destination-note').getBoundingClientRect().bottom<=document.querySelector('.settings-controls').getBoundingClientRect().bottom})")
                Path(args.smoke_test).write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
            finally:
                window.destroy()
    try:
        webview.start(started, gui="edgechromium", private_mode=True, storage_path=str(DATA / "webview" / str(os.getpid())), icon=str(ROOT / "assets" / "revela.ico"))
    except Exception as error:
        logging.exception("Startup failed")
        ctypes.windll.user32.MessageBoxW(0, f"Revela no pudo abrirse. Comprueba que Microsoft Edge WebView2 esté instalado.\n\n{error}", "Revela", 0x10)


if __name__ == "__main__":
    main()
