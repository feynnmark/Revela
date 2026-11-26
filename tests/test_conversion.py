import hashlib
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageChops
from app import Api
from engine import Options, ConversionError, RAW_EXTENSIONS, convert, thumbnail


class ConversionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "foto á #1.png"
        image = Image.new("RGBA", (240, 160), (240, 90, 20, 128))
        exif = Image.Exif()
        exif[271] = "Test Camera"
        image.save(self.source, exif=exif)
        self.original = hashlib.sha256(self.source.read_bytes()).digest()

    def tearDown(self):
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).digest(), self.original)
        self.temp.cleanup()

    def test_all_output_formats_and_resize(self):
        for fmt in ("jpg", "webp", "png", "tiff"):
            with self.subTest(format=fmt):
                result = convert(self.source, Options(format=fmt, max_size=120))
                with Image.open(result["output"]) as image:
                    self.assertEqual(image.size, (120, 80))
                    self.assertTrue(image.info.get("icc_profile"))
                    self.assertEqual(image.getexif().get(271), "Test Camera")
                    self.assertEqual("A" in image.getbands(), fmt != "jpg")

    def test_collision_and_source_protection(self):
        options = Options(format="png", destination=str(self.root))
        a = convert(self.source, options)
        b = convert(self.source, options)
        self.assertNotEqual(a["output"], str(self.source))
        self.assertNotEqual(a["output"], b["output"])
        self.assertEqual(Path(a["output"]).name, "foto á #1 (1).png")

    def test_two_simultaneous_conversions_never_collide(self):
        from concurrent.futures import ThreadPoolExecutor
        options = Options(format="webp", destination=str(self.root))
        with ThreadPoolExecutor(2) as pool:
            results = list(pool.map(lambda _: convert(self.source, options), range(2)))
        self.assertNotEqual(results[0]["output"], results[1]["output"])
        for result in results:
            with Image.open(result["output"]) as image:
                image.verify()

    def test_exif_orientation_is_applied_and_not_reapplied(self):
        source = self.root / "rotated.jpg"
        image = Image.new("RGB", (80, 40), "red")
        exif = Image.Exif()
        exif[274] = 6
        image.save(source, exif=exif)
        result = convert(source, Options(format="png"))
        with Image.open(result["output"]) as output:
            self.assertEqual(output.size, (40, 80))
            self.assertNotIn(274, output.getexif())

    def test_remove_metadata_and_do_not_upscale(self):
        result = convert(self.source, Options(format="webp", max_size=4000, metadata=False))
        with Image.open(result["output"]) as image:
            self.assertEqual(image.size, (240, 160))
            self.assertFalse(image.getexif())
            self.assertTrue(image.info.get("icc_profile"))

    def test_lossless_webp_keeps_pixels(self):
        result = convert(self.source, Options(format="webp", lossless=True))
        with Image.open(result["output"]) as output, Image.open(self.source) as original:
            self.assertIsNone(ImageChops.difference(output.convert("RGBA"), original).getbbox())

    def test_jpg_white_transparent_background(self):
        source = self.root / "transparent.png"
        Image.new("RGBA", (40, 40), (0, 0, 0, 0)).save(source)
        result = convert(source, Options())
        with Image.open(result["output"]) as image:
            self.assertEqual(image.getpixel((10,10)), (255,255,255))

    def test_cancel_before_commit_leaves_no_output(self):
        folder = self.root / "cancelled"
        result = convert(self.source, Options(destination=str(folder)), lambda: True)
        self.assertTrue(result["cancelled"])
        self.assertEqual(list(folder.iterdir()), [])

    def test_first_frame_is_reported(self):
        source = self.root / "animation.gif"
        Image.new("RGB", (40,40), "red").save(source, save_all=True, append_images=[Image.new("RGB", (40,40), "blue")], duration=100)
        result = convert(source, Options(format="png"))
        self.assertIn("primer fotograma", result["note"])
        with Image.open(result["output"]) as image:
            self.assertEqual(image.getpixel((10,10)), (255,0,0))

    def test_settings_validation(self):
        for values in ({"format":"exe"},{"quality":0},{"quality":101},{"max_size":-1},{"destination":"relative"}):
            with self.subTest(values=values), self.assertRaises(ConversionError):
                Options.parse(values)

    def test_corrupt_file_isolated_in_batch_and_duplicates_removed(self):
        corrupt = self.root / "corrupt.jpg"
        corrupt.write_text("not a photo")
        api = Api(self.root / "settings.json")
        api.add_paths([str(corrupt), str(self.source), str(self.source)])
        self.wait_for(lambda: not api.get_state()["scanning"])
        self.assertEqual(len(api.get_state()["files"]), 2)
        api.update_settings({"format":"webp"})
        api.start_batch()
        self.wait_for(lambda: not api.get_state()["busy"])
        data = api.get_state()
        self.assertEqual(data["batch"]["completed"], 1)
        self.assertEqual(data["batch"]["errors"], 1)
        self.assertTrue(data["files"][0]["error"])
        self.assertEqual(data["files"][1]["state"], "done")
        self.assertEqual(Api(self.root / "settings.json").get_state()["settings"]["format"], "webp")

    def test_cancellation_keeps_pending_queue_and_settings_frozen(self):
        api = Api(self.root / "settings.json")
        api.add_paths([str(self.source)])
        self.wait_for(lambda: not api.get_state()["scanning"])
        entered, release = threading.Event(), threading.Event()
        def blocked_conversion(path, options, cancelled):
            entered.set()
            release.wait(5)
            return convert(path, options, cancelled)
        with patch("app.convert", blocked_conversion):
            api.start_batch()
            self.assertTrue(entered.wait(5))
            self.assertIn("error", api.update_settings({"format":"png"}))
            api.cancel_batch()
            release.set()
            self.wait_for(lambda: not api.get_state()["busy"])
        data = api.get_state()
        self.assertTrue(data["batch"]["cancelled"])
        self.assertEqual(data["files"][0]["state"], "pending")
        self.assertEqual(data["batch"]["completed"], 0)

    def test_recursion_skips_revela_outputs(self):
        folder = self.root / "Revela"
        folder.mkdir()
        Image.new("RGB", (10,10)).save(folder / "already.jpg")
        api = Api(self.root / "settings.json")
        api.add_paths([str(self.root)])
        self.wait_for(lambda: not api.get_state()["scanning"])
        self.assertEqual(len(api.get_state()["files"]), 1)

    @staticmethod
    def wait_for(condition):
        deadline = time.monotonic() + 20
        while not condition():
            if time.monotonic() > deadline:
                raise AssertionError("La tarea no terminó a tiempo")
            time.sleep(.02)


class RealRawTests(unittest.TestCase):
    def test_available_raw_fixtures(self):
        fixture_dir = Path(os.environ.get("REVELA_RAW_FIXTURES", Path(__file__).resolve().parents[1] / ".local" / "fixtures"))
        fixtures = [p for p in fixture_dir.glob("*") if p.is_file() and p.suffix.lower() in RAW_EXTENSIONS]
        if not fixtures:
            self.skipTest("Descarga los fixtures indicados en TESTING.md para probar RAW reales.")
        with tempfile.TemporaryDirectory() as temporary:
            for source in fixtures:
                with self.subTest(file=source.name):
                    before = hashlib.sha256(source.read_bytes()).digest()
                    preview = thumbnail(source)
                    self.assertTrue(preview["image"].startswith("data:image/jpeg;base64,"))
                    for fmt in ("jpg", "webp"):
                        result = convert(source, Options(format=fmt, max_size=1600, destination=temporary))
                        with Image.open(result["output"]) as output:
                            self.assertEqual(output.mode, "RGB")
                            self.assertLessEqual(max(output.size), 1600)
                            self.assertGreater(min(output.size), 0)
                            output.verify()
                    self.assertEqual(before, hashlib.sha256(source.read_bytes()).digest())


if __name__ == "__main__":
    unittest.main()
