"""Draw the app's own geometric R mark; no generated or third-party artwork."""
from pathlib import Path
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[1]
size = 256
image = Image.new("RGBA", (size, size))
d = ImageDraw.Draw(image)
d.rounded_rectangle((8, 8, 248, 248), radius=55, fill="#ece9e1")
d.line([(82, 180), (82, 76), (127, 76)], fill="#171717", width=18)
d.arc((94, 76, 174, 142), -90, 90, fill="#171717", width=18)
d.line([(82, 142), (136, 142), (178, 184)], fill="#171717", width=18)
d.ellipse((172, 48, 198, 74), fill="#957449")
image.save(root / "assets" / "revela.ico", sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
image.save(root / "assets" / "revela.png")
