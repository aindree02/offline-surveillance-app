# test_plate_accuracy.py
# Standalone, fast OCR evaluation for number plates with robust normalization + fuzzy match.

# --- macOS OpenMP fix (put BEFORE torch/easyocr import) ---
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"   # workaround for duplicate libomp on macOS
os.environ["OMP_NUM_THREADS"] = "1"           # keep CPU usage sane

import re
import csv
from pathlib import Path
from difflib import get_close_matches

import easyocr
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report

# =========================
# Config
# =========================
TEST_KNOWN_DIR = Path("test_plates/known")
TEST_UNKNOWN_DIR = Path("test_plates/unknown")
PLATE_MAP_CSV  = Path("plate_owner_mapping.csv")  # must contain a plate column

# OCR + matching
RECOGNITION_CONF_MIN = 0.30   # drop low-confidence OCR tokens (0..1)
FUZZY_CUTOFF          = 0.62  # lower = more tolerant to OCR typos (0..1)
VALID_EXTS            = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".jfif"}

# Regex for plate-like tokens (adjust for your locale if needed)
PLATE_TOKEN = re.compile(r"[A-Z0-9]{5,}", re.IGNORECASE)

# Save plots
SAVE_DIR = Path("reports")
SAVE_DIR.mkdir(parents=True, exist_ok=True)
SAVE_CONFUSION = True

# =========================
# Helpers
# =========================
def list_images_recursive(root: Path):
    files = []
    if not root.exists():
        return files
    for dp, _, fns in os.walk(root):
        for f in fns:
            if Path(f).suffix.lower() in VALID_EXTS:
                files.append(str(Path(dp) / f))
    return sorted(files)

def load_plate_map(csv_path: Path):
    """
    Load known plates from CSV. Accepts common column names.
    Normalizes: uppercase, strips non-alphanumerics, applies substitution map.
    """
    known_plates = set()
    if not csv_path.exists():
        print(f"[WARN] Mapping file not found: {csv_path}")
        return known_plates

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        keys = reader.fieldnames or []
        col = None
        for k in ("plate", "Plate", "plate_number", "PlateNumber"):
            if k in keys:
                col = k
                break
        if col is None:
            print(f"[WARN] No plate column found. Columns in CSV: {keys}")
            return known_plates

        for row in reader:
            raw = (row.get(col) or "").upper()
            norm = normalize_plate_text(raw)
            if norm:
                known_plates.add(norm)
    return known_plates

# Common OCR confusions mapping
CHAR_SUBS = {
    "0": "O", "O": "O",
    "1": "I", "I": "I", "l": "I",
    "8": "B", "B": "B",
    "5": "S", "S": "S",
    "2": "Z", "Z": "Z",
    "4": "A", "A": "A",
    "6": "G", "G": "G",
    "7": "T", "T": "T",
}

def normalize_plate_text(s: str) -> str:
    """
    Uppercase, remove non-alphanumerics, and map commonly-confused chars to a canonical set.
    This reduces false 'unknown' due to O/0, I/1, B/8, etc.
    """
    s = re.sub(r"[^A-Z0-9]", "", s.upper())
    out = []
    for ch in s:
        if ch in CHAR_SUBS:
            out.append(CHAR_SUBS[ch])
        else:
            out.append(ch)
    return "".join(out)

def ocr_candidates(reader, img_path: str):
    """
    Return list of normalized candidate strings from OCR for one image.
    - Filters by min confidence
    - Prefers tokens that look like plates
    - Falls back to longest high-confidence token
    """
    try:
        results = reader.readtext(img_path, detail=1)  # (bbox, text, conf)
        cands, high_conf = [], []
        for _, text, conf in results:
            if conf is None or conf < RECOGNITION_CONF_MIN:
                continue
            norm = normalize_plate_text(text)
            if not norm:
                continue
            high_conf.append(norm)
            if PLATE_TOKEN.fullmatch(norm):
                cands.append(norm)
        if not cands and high_conf:
            cands.append(sorted(high_conf, key=len, reverse=True)[0])
        return cands
    except Exception as e:
        print(f"[OCR-ERR] {img_path}: {e}")
        return []

def classify_plate(preds, known_plates):
    """
    Binary decision: 'known' if any candidate is an exact or fuzzy match; else 'unknown'.
    """
    for p in preds:
        if p in known_plates:
            return "known", p, "exact"
        # fuzzy against known plates
        match = get_close_matches(p, list(known_plates), n=1, cutoff=FUZZY_CUTOFF)
        if match:
            return "known", p, f"fuzzy→{match[0]}"
    return "unknown", preds[0] if preds else "", "none"

# =========================
# Load data
# =========================
reader = easyocr.Reader(['en'], gpu=False)
known_plate_set = load_plate_map(PLATE_MAP_CSV)

known_imgs   = list_images_recursive(TEST_KNOWN_DIR)
unknown_imgs = list_images_recursive(TEST_UNKNOWN_DIR)

print(f"\nKnown plate images   : {len(known_imgs)}")
print(f"Unknown plate images : {len(unknown_imgs)}")
print(f"Known plates in CSV  : {len(known_plate_set)}")

# =========================
# Evaluate
# =========================
y_true, y_pred = [], []
known_total = unknown_total = 0
known_correct = unknown_correct = 0

print("\n=== Testing KNOWN plates ===")
for img in known_imgs:
    preds = ocr_candidates(reader, img)
    cls, used, how = classify_plate(preds, known_plate_set)
    print(f"[Known]   {os.path.basename(img)} -> {preds} => {cls} ({how})")
    known_total += 1
    if cls == "known":
        known_correct += 1
        y_pred.append("known")
    else:
        y_pred.append("unknown")
    y_true.append("known")

print("\n=== Testing UNKNOWN plates ===")
for img in unknown_imgs:
    preds = ocr_candidates(reader, img)
    cls, used, how = classify_plate(preds, known_plate_set)
    print(f"[Unknown] {os.path.basename(img)} -> {preds} => {cls} ({how})")
    unknown_total += 1
    if cls == "unknown":
        unknown_correct += 1
        y_pred.append("unknown")
    else:
        y_pred.append("known")
    y_true.append("unknown")

def pct(n, d):
    return (100.0 * n / d) if d else 0.0

known_acc   = pct(known_correct, known_total)
unknown_acc = pct(unknown_correct, unknown_total)
overall_acc = pct(known_correct + unknown_correct, known_total + unknown_total)

print("\n=== Number Plate OCR Accuracy Results ===")
print(f"Known Plates Accuracy   : {known_acc:.2f}% ({known_correct}/{known_total})")
print(f"Unknown Plates Accuracy : {unknown_acc:.2f}% ({unknown_correct}/{unknown_total})")
print(f"Overall Accuracy        : {overall_acc:.2f}%")

# =========================
# Confusion Matrix + Report
# =========================
cm = confusion_matrix(y_true, y_pred, labels=["known", "unknown"])

plt.figure()
sns.heatmap(cm, annot=True, fmt='d', cmap="Greens",
            xticklabels=["Predicted: Known", "Predicted: Unknown"],
            yticklabels=["Actual: Known", "Actual: Unknown"])
plt.title("Number Plate Recognition Confusion Matrix")
plt.xlabel("Prediction"); plt.ylabel("Actual")
plt.tight_layout()
if SAVE_CONFUSION:
    out_path = SAVE_DIR / "plate_confusion_matrix.png"
    plt.savefig(out_path, dpi=300)
    print(f"[Saved] Confusion matrix -> {out_path}")
plt.show()

print("\nClassification Report:\n")
print(classification_report(y_true, y_pred, target_names=["Known", "Unknown"]))
