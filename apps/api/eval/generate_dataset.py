"""Generate a deterministic synthetic labelled dataset (images + ground-truth JSON).

Everything is fictional: merchants, people and ID numbers are made up and ID cards are
marked SPECIMEN. Re-running with the same seed reproduces identical labels.

    python -m eval.generate_dataset
"""

import json
import random
from datetime import date, timedelta
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

DATA = Path(__file__).parent / "data"
SEED = 7

MERCHANTS = [
    ("Blue Heron Cafe", "12 Harbor St, Portland, ME 04101"),
    ("Greenfield Market", "450 Oak Ave, Austin, TX 78701"),
    ("Northside Hardware", "98 Mill Rd, Denver, CO 80202"),
    ("Sunrise Bakery", "7 Elm Ct, Boise, ID 83702"),
    ("Pixel Print Shop", "301 Main St, Madison, WI 53703"),
    ("Cedar & Stone Books", "22 River Ln, Asheville, NC 28801"),
]
ITEMS = [
    ("Latte", 4.50),
    ("Bagel", 2.75),
    ("Whole Milk 1gal", 3.99),
    ("Sourdough Loaf", 6.25),
    ("Paper Towels", 8.49),
    ("Cable Ties", 5.99),
    ("Notebook A5", 7.20),
    ("Green Tea", 3.25),
    ("Cheddar Block", 5.80),
    ("Orange Juice", 4.10),
    ("Screwdriver Set", 14.99),
    ("Bananas", 1.89),
]
PAYMENTS = ["VISA ****1234", "Cash", "MASTERCARD ****9876", "Debit ****4411"]
NAMES = [
    ("ALEX RIVERA", "123 Sample Rd, Springfield, IL 62701", "Driver License"),
    ("JORDAN LEE", "88 Test Blvd, Fairview, OR 97024", "Driver License"),
    ("SAM PATEL", "5 Demo Way, Lakeside, MN 55369", "State ID"),
    ("CASEY MORGAN", "41 Fiction Ave, Riverton, UT 84065", "State ID"),
]


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.load_default(size=size)


def make_receipt(rng: random.Random, idx: int) -> tuple[Image.Image, dict]:
    name, addr = rng.choice(MERCHANTS)
    d = date(2025, 1, 1) + timedelta(days=rng.randrange(0, 600))
    chosen = rng.sample(ITEMS, rng.randint(2, 6))
    items = []
    for desc, price in chosen:
        qty = rng.choice([1, 1, 1, 2, 3])
        items.append(
            {
                "description": desc,
                "quantity": qty,
                "unit_price": price,
                "total": round(qty * price, 2),
            }
        )
    subtotal = round(sum(i["total"] for i in items), 2)
    tax = round(subtotal * 0.08, 2)
    tip = round(subtotal * 0.15, 2) if name.endswith("Cafe") else None
    total = round(subtotal + tax + (tip or 0), 2)
    pay = rng.choice(PAYMENTS)

    label = {
        "merchant_name": name,
        "merchant_address": addr,
        "date": d.isoformat(),
        "currency": "USD",
        "items": items,
        "subtotal": subtotal,
        "tax": tax,
        "tip": tip,
        "total": total,
        "payment_method": pay,
    }

    lines = [(name, 26), (addr, 14), (f"Date: {d.strftime('%m/%d/%Y')}", 15), ("", 10)]
    for i in items:
        txt = (
            i["description"]
            if i["quantity"] == 1
            else (f"{i['description']}  {i['quantity']} x {i['unit_price']:.2f}")
        )
        lines.append((f"{txt}|{i['total']:.2f}", 16))
    lines += [("", 10), (f"Subtotal|{subtotal:.2f}", 16), (f"Tax (8%)|{tax:.2f}", 16)]
    if tip is not None:
        lines.append((f"Tip|{tip:.2f}", 16))
    lines += [(f"TOTAL|{total:.2f}", 20), ("", 10), (f"Paid: {pay}", 15), ("Thank you!", 15)]

    w = 460
    h = 40 + sum(s + 12 for _, s in lines)
    img = Image.new("RGB", (w, h), (250, 250, 247))
    dr = ImageDraw.Draw(img)
    y = 20
    for text, size in lines:
        f = font(size)
        if "|" in text:
            left, right = text.split("|")
            dr.text((24, y), left, fill=(20, 20, 20), font=f)
            dr.text((w - 24, y), right, fill=(20, 20, 20), font=f, anchor="ra")
        else:
            x = w // 2 if size >= 20 else 24
            dr.text((x, y), text, fill=(20, 20, 20), font=f, anchor="ma" if size >= 20 else "la")
        y += size + 12

    # Every 3rd receipt is degraded (rotation + blur + shifted background) to be harder.
    if idx % 3 == 2:
        img = img.rotate(rng.uniform(-4, 4), expand=True, fillcolor=(190, 190, 185))
        img = img.filter(ImageFilter.GaussianBlur(0.9))
    return img, label


def make_id(rng: random.Random, idx: int) -> tuple[Image.Image, dict]:
    name, addr, kind = NAMES[idx % len(NAMES)]
    dob = date(1975, 1, 1) + timedelta(days=rng.randrange(0, 9000))
    exp = date(2028, 1, 1) + timedelta(days=rng.randrange(0, 1500))
    num = f"{rng.choice('ABCDEFGH')}{rng.randrange(10**7, 10**8)}"
    label = {
        "document_type": kind,
        "full_name": name.title(),
        "document_number": num,
        "date_of_birth": dob.isoformat(),
        "expiry_date": exp.isoformat(),
        "nationality": None,
        "address": addr,
    }
    img = Image.new("RGB", (640, 400), (214, 228, 240))
    dr = ImageDraw.Draw(img)
    dr.rectangle([0, 0, 640, 56], fill=(40, 70, 120))
    dr.text((20, 14), f"SPECIMEN - {kind.upper()}", fill="white", font=font(26))
    dr.rectangle([24, 90, 164, 260], fill=(160, 170, 185))
    rows = [
        ("NAME", name.title()),
        ("DOC NO", num),
        ("DOB", dob.strftime("%m/%d/%Y")),
        ("EXPIRES", exp.strftime("%m/%d/%Y")),
        ("ADDRESS", addr),
    ]
    y = 80
    for k, v in rows:
        dr.text((190, y), k, fill=(70, 80, 100), font=font(13))
        dr.text((190, y + 15), v, fill=(10, 10, 10), font=font(20))
        y += 52
    return img, label


def main() -> None:
    rng = random.Random(SEED)
    manifest = []
    for kind, n, maker in [("receipt", 18, make_receipt), ("id", 4, make_id)]:
        out = DATA / kind
        out.mkdir(parents=True, exist_ok=True)
        for i in range(n):
            img, label = maker(rng, i)
            stem = f"{kind}_{i:02d}"
            img.save(out / f"{stem}.png", optimize=True)
            (out / f"{stem}.json").write_text(json.dumps(label, indent=2) + "\n")
            manifest.append(
                {"doc_type": kind, "image": f"{kind}/{stem}.png", "label": f"{kind}/{stem}.json"}
            )
    (DATA / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wrote {len(manifest)} labelled documents to {DATA}")


if __name__ == "__main__":
    main()
