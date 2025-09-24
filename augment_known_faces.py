# augment_known_faces.py
import os
from PIL import Image, ImageEnhance, ImageOps

INPUT_ROOT = "known_faces"          # your existing known faces root
OUTPUT_ROOT = "known_faces"         # write alongside originals
# OUTPUT_ROOT = "known_faces_augmented"  # <- use this instead if you want a separate folder

AUG_SUFFIXES = ("_rot10", "_rot-10", "_flip", "_bright")

def ensure_dir(p):
    os.makedirs(p, exist_ok=True)

def is_image(fname):
    return fname.lower().endswith((".jpg", ".jpeg", ".png"))

def already_augmented(fname):
    base, _ = os.path.splitext(fname)
    return base.endswith(AUG_SUFFIXES)

for person in os.listdir(INPUT_ROOT):
    in_person_dir = os.path.join(INPUT_ROOT, person)
    if not os.path.isdir(in_person_dir):
        continue

    out_person_dir = os.path.join(OUTPUT_ROOT, person)
    ensure_dir(out_person_dir)

    for fname in os.listdir(in_person_dir):
        if not is_image(fname) or already_augmented(fname):
            continue

        src_path = os.path.join(in_person_dir, fname)
        base, ext = os.path.splitext(fname)

        try:
            # Open & normalize mode/EXIF
            with Image.open(src_path) as img:
                # Correct orientation from EXIF if present
                img = ImageOps.exif_transpose(img)
                # Convert to RGB to avoid "wrong mode" errors
                img = img.convert("RGB")

                # 1) Rotate +10°
                img.rotate(10, expand=True).save(
                    os.path.join(out_person_dir, f"{base}_rot10{ext}")
                )

                # 2) Rotate -10°
                img.rotate(-10, expand=True).save(
                    os.path.join(out_person_dir, f"{base}_rot-10{ext}")
                )

                # 3) Horizontal flip
                img.transpose(Image.FLIP_LEFT_RIGHT).save(
                    os.path.join(out_person_dir, f"{base}_flip{ext}")
                )

                # 4) Brightness +15%
                ImageEnhance.Brightness(img).enhance(1.15).save(
                    os.path.join(out_person_dir, f"{base}_bright{ext}")
                )

        except Exception as e:
            print(f"⚠️ Skipped {src_path}: {e}")

print("✅ Augmentation complete. Now re-run generate_encodings.py to update encodings.pkl")

