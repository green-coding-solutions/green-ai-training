"""Generates the static shop site served in the text-compression benchmark (deterministic).

site/index.html, site/app.js, site/style.css, site/data/products.json plus precompressed .gz copies
(gzip -9, written once here) for the gzip_static variant. Needs only the standard library.
"""
import gzip
import json
import random
from pathlib import Path

SITE = Path(__file__).resolve().parent / "site"
rng = random.Random(7)
CATEGORIES = ["bikes", "helmets", "lights", "locks", "bags", "tools", "tires", "apparel"]
ADJECTIVES = ["light", "urban", "trail", "compact", "pro", "classic", "eco", "touring"]


def products(n=1500):
    for i in range(n):
        cat = rng.choice(CATEGORIES)
        yield {
            "id": i + 1,
            "sku": f"{cat[:3].upper()}-{i:05d}",
            "name": f"{rng.choice(ADJECTIVES).title()} {cat[:-1].title()} {rng.randint(1, 99)}",
            "category": cat,
            "price_cents": rng.randint(499, 249900),
            "stock": rng.randint(0, 250),
            "rating": round(rng.uniform(2.5, 5.0), 1),
            "tags": rng.sample(ADJECTIVES, 3),
            "image": f"/img/{cat}/{i + 1}.webp",
        }


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = text.encode("utf-8")
    path.write_bytes(data)
    path.with_name(path.name + ".gz").write_bytes(gzip.compress(data, compresslevel=9, mtime=0))
    print(f"{path.relative_to(SITE)}: {len(data) // 1024} KB")


def main():
    items = list(products())
    write(SITE / "data/products.json", json.dumps(items))

    cards = "\n".join(
        f'<article class="card"><img src="{p["image"]}" alt="{p["name"]}" loading="lazy" width="320" height="240">'
        f'<h3>{p["name"]}</h3><p class="price">€{p["price_cents"] / 100:.2f}</p>'
        f'<button class="btn btn-cart" data-sku="{p["sku"]}">Add to cart</button></article>'
        for p in items[:200]
    )
    write(SITE / "index.html", f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>Bike Shop</title>
<link rel="stylesheet" href="/style.css"><script defer src="/app.js"></script></head>
<body><header class="site-header"><a class="logo" href="/">Bike Shop</a></header>
<main class="grid">
{cards}
</main></body></html>
""")

    functions = []
    for i in range(400):
        name = f"handle{rng.choice(CATEGORIES).title()}{i}"
        functions.append(f"""export function {name}(state, event) {{
  // update the {rng.choice(CATEGORIES)} view after a user interaction
  const items = state.items.filter((item) => item.category === event.category && item.stock > {rng.randint(0, 5)});
  const total = items.reduce((sum, item) => sum + item.price_cents, 0);
  return {{ ...state, items, total, updatedAt: Date.now(), source: "{name}" }};
}}
""")
    write(SITE / "app.js", "\n".join(functions))

    rules = []
    for cat in CATEGORIES:
        for variant in ("", "-featured", "-sale", "-soldout"):
            for el in ("card", "badge", "price", "title", "button"):
                rules.append(f""".{cat}{variant} .{el} {{
  display: flex;
  padding: {rng.randint(2, 16)}px {rng.randint(4, 24)}px;
  color: #{rng.randint(0, 0xFFFFFF):06x};
  border: 1px solid #e2e8f0;
  border-radius: 6px;
}}
""")
    write(SITE / "style.css", "\n".join(rules))


if __name__ == "__main__":
    main()
