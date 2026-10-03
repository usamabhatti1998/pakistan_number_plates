# Turns the raw Roboflow/YOLO download into number_plates_annotations.csv
# (one row per annotation, plus one row for every image that has no labels)
# and draws the small contact sheet in charts/.
#
# usage: python prepare_annotations.py /path/to/extracted/dataset
# The folder must contain train/ valid/ test/, each with images/ and labels/.

import hashlib
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Rectangle
from PIL import Image

here = Path(__file__).resolve().parent
raw = Path(sys.argv[1]) if len(sys.argv) > 1 else here / "plates_raw"

# class names in the order given in data.yaml
names = [str(d) for d in range(10)] + list("ABCDEFGHIJKL") + ["LicensePlate"] + list("MNOPQRSTUVWXYZ")

rows = []
for split in ["train", "valid", "test"]:
    for img_path in sorted((raw / split / "images").glob("*")):
        m = re.match(r"(.*)\.rf\.([0-9a-f]+)$", img_path.stem)
        source_id, rf_hash = (m.group(1), m.group(2)) if m else (img_path.stem, "")
        data = img_path.read_bytes()
        with Image.open(img_path) as im:
            img_w, img_h = im.size
        base = {
            "split": split,
            "image_file": img_path.name,
            "source_id": source_id,
            "rf_hash": rf_hash,
            "image_bytes": len(data),
            "image_md5": hashlib.md5(data).hexdigest(),
            "img_width": img_w,
            "img_height": img_h,
        }

        label_path = raw / split / "labels" / (img_path.stem + ".txt")
        lines = []
        if label_path.exists():
            lines = [l.split() for l in label_path.read_text().splitlines() if l.strip()]

        if not lines:
            # keep the image in the table so unlabelled images are not lost
            rows.append({**base, "has_label_file": label_path.exists(), "box_index": -1})
            continue

        for i, parts in enumerate(lines):
            cls = int(parts[0])
            vals = [float(v) for v in parts[1:]]
            if len(vals) == 4:
                fmt, n_points = "box", 0
                xc, yc, w, h = vals
            else:
                # Roboflow segmentation row: class x1 y1 x2 y2 ... -> take the bounding box
                fmt, n_points = "polygon", len(vals) // 2
                xs, ys = vals[0::2], vals[1::2]
                xc, yc = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
                w, h = max(xs) - min(xs), max(ys) - min(ys)
            rows.append({
                **base,
                "has_label_file": True,
                "box_index": i,
                "class_id": cls,
                "class_name": names[cls] if 0 <= cls < len(names) else "",
                "x_center": round(xc, 6),
                "y_center": round(yc, 6),
                "width": round(w, 6),
                "height": round(h, 6),
                "label_format": fmt,
                "n_points": n_points,
                "n_values": len(vals),
            })

df = pd.DataFrame(rows)
df["class_id"] = df["class_id"].astype("Int64")
for c in ["n_points", "n_values"]:
    df[c] = df[c].astype("Int64")
df.to_csv(here / "number_plates_annotations.csv", index=False)
print(len(df), "rows,", df["image_file"].nunique(), "images")

# contact sheet: nine labelled images picked with a fixed seed, boxes drawn on top
boxes = df[df["box_index"] >= 0]
has_plate = boxes[boxes["class_name"] == "LicensePlate"]["image_file"].drop_duplicates()
picked = has_plate.sample(9, random_state=7).tolist()

fig, axes = plt.subplots(3, 3, figsize=(10, 10))
for ax, name in zip(axes.ravel(), picked):
    sub = boxes[boxes["image_file"] == name]
    split = sub["split"].iloc[0]
    with Image.open(raw / split / "images" / name) as im:
        ax.imshow(im.convert("RGB"))
        W, H = im.size
    for r in sub.itertuples():
        is_plate = r.class_name == "LicensePlate"
        ax.add_patch(Rectangle(((r.x_center - r.width / 2) * W, (r.y_center - r.height / 2) * H),
                               r.width * W, r.height * H, fill=False,
                               edgecolor="#d62728" if is_plate else "#00c8ff",
                               linewidth=2 if is_plate else 1.2))
    ax.set_title(f"{split}, {len(sub)} boxes", fontsize=10)
    ax.axis("off")
fig.suptitle("Nine sample images with their annotation boxes (red = plate, blue = characters)", fontsize=12)
fig.tight_layout()
(here / "charts").mkdir(exist_ok=True)
fig.savefig(here / "charts" / "00_sample_images_contact_sheet.png", dpi=150)
