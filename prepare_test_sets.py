import os, shutil, random
from pathlib import Path
from PIL import Image, ImageEnhance

# === CONFIG ===
KNOWN_DIR = Path("known_faces")
TEST_KNOWN_DIR = Path("test_faces/known")
TEST_UNKNOWN_DIR = Path("test_faces/unknown")

# percentage of images per person to HOLD OUT for testing (e.g., 0.2 = 20%)
HOLDOUT_PCT = 0.25
SEED = 42
MODE = "move"   # "move" (recommended) or "copy"
DO_AUGMENT = True
AUG_PER_IMAGE = 1           # how many slight variants per moved test image (0/1/2...)
UNKNOWN_SOURCE_DIRS = [
    Path("Unknown_faces"),  # use any folder(s) you already have with people NOT in known_faces
    Path("vehicle_images")  # add/remove paths as you like
]

# === HELPERS ===
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

def list_images(p: Path):
    return [x for x in p.iterdir() if x.suffix.lower() in IMG_EXTS and x.is_file()]

def ensure_dir(p: Path): p.mkdir(parents=True, exist_ok=True)

def augment_save(img_path: Path, out_dir: Path, idx: int):
    try:
        im = Image.open(img_path).convert("RGB")
        # small rotation
        angle = random.choice([-10, -7, -5, 5, 7, 10])
        im2 = im.rotate(angle, expand=True)
        # small brightness/contrast tweak
        im2 = ImageEnhance.Brightness(im2).enhance(random.uniform(0.9, 1.1))
        im2 = ImageEnhance.Contrast(im2).enhance(random.uniform(0.9, 1.1))
        base = img_path.stem
        im2.save(out_dir / f"{base}_aug{idx}.jpg", quality=92)
    except Exception as e:
        print(f"[AUG] skip {img_path.name}: {e}")

def move_or_copy(src: Path, dst: Path):
    ensure_dir(dst.parent)
    if MODE == "move":
        shutil.move(str(src), str(dst))
    else:
        shutil.copy2(str(src), str(dst))

random.seed(SEED)

# === 1) Split per-person known faces ===
print("\n=== HOLD-OUT KNOWN FACES FOR TEST ===")
for person_dir in sorted([d for d in KNOWN_DIR.iterdir() if d.is_dir()]):
    imgs = list_images(person_dir)
    if not imgs:
        continue
    k = max(1, int(len(imgs) * HOLDOUT_PCT))
    sample = random.sample(imgs, k)
    out_person = TEST_KNOWN_DIR / person_dir.name
    ensure_dir(out_person)
    moved = 0
    for i, img in enumerate(sample, 1):
        dst = out_person / img.name
        move_or_copy(img, dst)
        moved += 1
        if DO_AUGMENT and AUG_PER_IMAGE > 0:
            for aug_i in range(AUG_PER_IMAGE):
                augment_save(dst, out_person, aug_i)
    print(f"{person_dir.name}: moved {moved} to {out_person}")

# === 2) Build UNKNOWN test set from given source dirs ===
print("\n=== BUILD UNKNOWN TEST SET ===")
ensure_dir(TEST_UNKNOWN_DIR)
added = 0
for src_dir in UNKNOWN_SOURCE_DIRS:
    if not src_dir.exists():
        continue
    for img in list_images(src_dir):
        # Avoid name clashes
        dst = TEST_UNKNOWN_DIR / f"{img.stem}_unk{added}{img.suffix.lower()}"
        if MODE == "move" and src_dir.resolve().is_relative_to(KNOWN_DIR.resolve()):
            # never move from KNOWN_DIR into unknown by mistake
            continue
        shutil.copy2(str(img), str(dst))
        added += 1
print(f"Added {added} unknown test images to {TEST_UNKNOWN_DIR}")

print("\nDone. Now re-run:  python generate_encodings.py   (since we MOVED holdout images)")
print("Then evaluate with: python test_face_accuracy.py")
