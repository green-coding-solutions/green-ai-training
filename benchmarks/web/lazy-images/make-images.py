"""Generates the photo-like JPEGs referenced by test-cases/web/lazy-images/index.html.

Smooth color gradients plus film-grain noise give JPEGs of ~130 KB at 1600x1067, in the range of web-optimized photos.
Deterministic: the same files are produced on every run. Needs: pip install pillow
"""
import random
import re
from pathlib import Path

from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
TEST_CASE = HERE / "../../../test-cases/web/lazy-images"
WIDTH, HEIGHT = 1600, 1067


def make_image(seed, path):
    rng = random.Random(seed)
    top = [rng.randint(40, 220) for _ in range(3)]
    bottom = [rng.randint(20, 200) for _ in range(3)]
    small = Image.new("RGB", (32, 22))
    for y in range(22):
        for x in range(32):
            t = y / 21
            small.putpixel((x, y), tuple(
                int(top[c] * (1 - t) + bottom[c] * t + rng.randint(-25, 25)) for c in range(3)))
    img = small.resize((WIDTH, HEIGHT), Image.BICUBIC).filter(ImageFilter.GaussianBlur(6))
    noise = Image.effect_noise((WIDTH, HEIGHT), 24).convert("RGB")
    img = Image.blend(img, noise, 0.12)
    img.save(path, "JPEG", quality=82, optimize=True)


def main():
    html = (TEST_CASE / "index.html").read_text()
    names = sorted(set(re.findall(r'src="images/([^"]+\.jpg)"', html)))
    out = TEST_CASE / "images"
    out.mkdir(exist_ok=True)
    for i, name in enumerate(names):
        make_image(i, out / name)
        print(f"{name}: {(out / name).stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
