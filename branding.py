"""Single source for the sidebar mark, Windows window icon and EXE icon."""
from pathlib import Path
from PIL import Image, ImageDraw

PNG_NAME = "brand.png"
ICO_NAME = "brand.ico"


def draw_brand(size=512):
    image = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((0, 0, 511, 511), radius=126, fill="#8065E8")
    # Arrow + play: the mark stays readable in Explorer at 16–32 px.
    ink = "#FFFFFF"
    draw.line((216, 114, 216, 302), fill=ink, width=31)
    draw.line((138, 233, 216, 311, 294, 233), fill=ink, width=31, joint="curve")
    draw.rounded_rectangle((131, 359, 384, 388), radius=14, fill=ink)
    draw.polygon((326, 111, 326, 210, 411, 161), fill=ink)
    return image.resize((size, size), Image.Resampling.LANCZOS)


def generate_assets(directory=None):
    directory = Path(directory or Path(__file__).resolve().parent / "assets")
    directory.mkdir(parents=True, exist_ok=True)
    image = draw_brand()
    image.save(directory / PNG_NAME)
    image.save(directory / ICO_NAME, format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])


if __name__ == "__main__":
    generate_assets()
