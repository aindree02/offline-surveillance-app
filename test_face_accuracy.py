# test_face_accuracy.py
import os
import pickle
import numpy as np
import face_recognition
from pathlib import Path
from sklearn.metrics import confusion_matrix, classification_report
import matplotlib.pyplot as plt
import seaborn as sns

# ----------------------------
# Config
# ----------------------------
ENCODINGS_FILE = "encodings.pkl"
TEST_KNOWN_DIR = Path("test_faces/known")
TEST_UNKNOWN_DIR = Path("test_faces/unknown")

# Lower threshold = stricter match (typical range ~0.4–0.6)
THRESHOLD = 0.55

# If True, skip images where no face is found (doesn't count towards metrics)
# If False, treat "No Face Detected" as a misclassification for its class
SKIP_NO_FACE = True

VALID_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".jfif"}

# ----------------------------
# Helpers
# ----------------------------
def list_images_recursive(root: Path):
    files = []
    if not root.exists():
        return files
    for dp, _, fns in os.walk(root):
        for f in fns:
            if Path(f).suffix.lower() in VALID_EXTS:
                files.append(str(Path(dp) / f))
    return sorted(files)

def load_encodings(enc_path: str):
    with open(enc_path, "rb") as f:
        encs, names = pickle.load(f)
    return np.array(encs), np.array(names)

def recognize_face(image_path: str, known_encodings: np.ndarray, known_names: np.ndarray):
    try:
        image = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image)
        if len(encodings) == 0:
            return "No Face Detected"
        encoding = encodings[0]
        distances = face_recognition.face_distance(known_encodings, encoding)
        min_idx = int(np.argmin(distances))
        min_distance = float(distances[min_idx])
        if min_distance < THRESHOLD:
            return str(known_names[min_idx])
        else:
            return "Unknown"
    except Exception as e:
        return f"ERROR::{e.__class__.__name__}"

# ----------------------------
# Load encodings
# ----------------------------
known_encodings, known_names = load_encodings(ENCODINGS_FILE)

# ----------------------------
# Collect test images
# ----------------------------
known_imgs = list_images_recursive(TEST_KNOWN_DIR)
unknown_imgs = list_images_recursive(TEST_UNKNOWN_DIR)
print(f"\nFound {len(known_imgs)} known test images and {len(unknown_imgs)} unknown test images.")

# ----------------------------
# Evaluation
# ----------------------------
y_true, y_pred = [], []
known_correct = known_total = 0
unknown_correct = unknown_total = 0
skipped = errors = 0

print("\n=== Testing Known Faces ===")
for path in known_imgs:
    res = recognize_face(path, known_encodings, known_names)
    base = os.path.basename(path)
    if res == "No Face Detected" and SKIP_NO_FACE:
        skipped += 1
        continue
    if res.startswith("ERROR::") and SKIP_NO_FACE:
        errors += 1
        continue

    print(f"[Known] {base} -> {res}")
    known_total += 1
    if res != "Unknown" and not res.startswith("ERROR::"):
        known_correct += 1
        y_pred.append("known")
    else:
        y_pred.append("unknown")
    y_true.append("known")

print("\n=== Testing Unknown Faces ===")
for path in unknown_imgs:
    res = recognize_face(path, known_encodings, known_names)
    base = os.path.basename(path)
    if res == "No Face Detected" and SKIP_NO_FACE:
        skipped += 1
        continue
    if res.startswith("ERROR::") and SKIP_NO_FACE:
        errors += 1
        continue

    print(f"[Unknown] {base} -> {res}")
    unknown_total += 1
    if res == "Unknown":
        unknown_correct += 1
        y_pred.append("unknown")
    else:
        y_pred.append("known")
    y_true.append("unknown")

def pct(n, d):
    return (100.0 * n / d) if d else 0.0

known_acc = pct(known_correct, known_total)
unknown_acc = pct(unknown_correct, unknown_total)
overall_acc = pct(known_correct + unknown_correct, known_total + unknown_total)

print("\n=== Face Recognition Accuracy Results ===")
print(f"Known Faces Accuracy   : {known_acc:.2f}% ({known_correct}/{known_total})")
print(f"Unknown Faces Accuracy : {unknown_acc:.2f}% ({unknown_correct}/{unknown_total})")
print(f"Overall Accuracy       : {overall_acc:.2f}%")
if SKIP_NO_FACE:
    print(f"Skipped (no face / read error): {skipped + errors} images")

# Confusion Matrix + Report
if y_true and y_pred:
    cm = confusion_matrix(y_true, y_pred, labels=["known", "unknown"])
    plt.figure()
    sns.heatmap(cm, annot=True, fmt='d', cmap="Blues",
                xticklabels=["Predicted: Known", "Predicted: Unknown"],
                yticklabels=["Actual: Known", "Actual: Unknown"])
    plt.title("Face Recognition Confusion Matrix")
    plt.xlabel("Prediction")
    plt.ylabel("Actual")
    plt.tight_layout()
    plt.show()

    print("\nClassification Report:\n")
    print(classification_report(y_true, y_pred, target_names=["Known", "Unknown"]))
else:
    print("\nNot enough classified samples to build a confusion matrix.")

