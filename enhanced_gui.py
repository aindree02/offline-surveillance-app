import cv2
import face_recognition
import numpy as np
import os
import subprocess
from datetime import datetime
import csv
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import threading
import pickle
import time

# ===================================================
# Configuration and Setup
# ===================================================
KNOWN_FACES_DIR = "known_faces"
UNKNOWN_DIR = "Unknown_faces"
LOG_FILE = "unknown_faces_log.csv"
ENCODING_FILE = "encodings.pkl"

# Load encodings
if not os.path.exists(ENCODING_FILE):
    raise FileNotFoundError("encodings.pkl not found! Please generate it first.")

with open(ENCODING_FILE, "rb") as f:
    known_encodings, known_names = pickle.load(f)

print(f"[INFO] Loaded {len(known_encodings)} known encodings from file.")

# Cooldown tracking
saved_faces = []
last_unknown_time = 0
cooldown_seconds = 5
known_count = 0
unknown_count = 0

os.makedirs(UNKNOWN_DIR, exist_ok=True)
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Date", "Time", "Saved Image Name"])

video_capture = None
running = False

# ===================================================
# GUI Setup
# ===================================================
window = tk.Tk()
window.title("Smart Surveillance System")
window.geometry("1000x800")
window.configure(bg="#1e1e1e")

video_label = tk.Label(window, bg="#1e1e1e")
video_label.pack(pady=10)

status_label = tk.Label(window, text="Status: Idle", font=("Helvetica", 12), fg="white", bg="#1e1e1e")
status_label.pack(pady=5)

counter_label = tk.Label(window, text="Known: 0  |  Unknown: 0", font=("Helvetica", 12), fg="white", bg="#1e1e1e")
counter_label.pack(pady=5)

snapshot_preview = tk.Label(window, bg="#1e1e1e")
snapshot_preview.pack(pady=10)

update_thread = None

# ===================================================
# Utility Functions
# ===================================================
def open_unknown_folder():
    subprocess.Popen(["open", UNKNOWN_DIR])

def open_log_file():
    subprocess.Popen(["open", LOG_FILE])

def update_counters():
    counter_label.config(text=f"Known: {known_count}  |  Unknown: {unknown_count}")

# ===================================================
# Surveillance Loop
# ===================================================
def surveillance_loop():
    global running, video_capture, last_unknown_time, known_count, unknown_count
    while running:
        ret, frame = video_capture.read()
        if not ret:
            time.sleep(0.05)
            continue

        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(known_encodings, face_encoding)
            name = "Unknown"

            face_distances = face_recognition.face_distance(known_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)

            if matches[best_match_index]:
                name = known_names[best_match_index]
                known_count += 1

            if name == "Unknown":
                is_new = True
                for saved in saved_faces:
                    similarity = np.dot(face_encoding, saved) / (np.linalg.norm(face_encoding) * np.linalg.norm(saved))
                    if similarity > 0.97:
                        is_new = False
                        break

                current_time = time.time()
                if is_new and current_time - last_unknown_time > cooldown_seconds:
                    saved_faces.append(face_encoding)
                    last_unknown_time = current_time
                    unknown_count += 1

                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"unknown_{timestamp}.jpg"
                    path = os.path.join(UNKNOWN_DIR, filename)
                    cv2.imwrite(path, frame)

                    with open(LOG_FILE, mode='a', newline='') as file:
                        writer = csv.writer(file)
                        writer.writerow([
                            datetime.now().strftime("%Y-%m-%d"),
                            datetime.now().strftime("%H:%M:%S"),
                            filename
                        ])

                    img_preview = Image.open(path).resize((150, 100))
                    preview_img = ImageTk.PhotoImage(img_preview)
                    snapshot_preview.configure(image=preview_img)
                    snapshot_preview.image = preview_img

            top *= 4
            right *= 4
            bottom *= 4
            left *= 4
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

        update_counters()
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        imgtk = ImageTk.PhotoImage(image=img)
        video_label.imgtk = imgtk
        video_label.configure(image=imgtk)

        window.update_idletasks()
        window.update()
        time.sleep(0.05)

# ===================================================
# Button Callbacks
# ===================================================
def start_surveillance():
    global video_capture, running, update_thread
    if not running:
        video_capture = cv2.VideoCapture(0)
        running = True
        status_label.config(text="Status: Monitoring", fg="lightgreen")
        start_button.config(state="disabled")
        update_thread = threading.Thread(target=surveillance_loop)
        update_thread.start()

def stop_surveillance():
    global video_capture, running, update_thread, known_count, unknown_count, saved_faces
    if running:
        running = False
        update_thread.join(timeout=1)
        if video_capture:
            video_capture.release()
        video_label.config(image='')
        snapshot_preview.config(image='')
        status_label.config(text="Status: Idle", fg="white")
        start_button.config(state="normal")
        known_count = 0
        unknown_count = 0
        saved_faces = []
        update_counters()

# ===================================================
# GUI Buttons
# ===================================================
button_frame = tk.Frame(window, bg="#1e1e1e")
button_frame.pack(pady=15)

button_font = ("Helvetica", 14, "bold")

start_button = tk.Button(
    button_frame, text="▶ Start Surveillance", command=start_surveillance,
    bg="green", fg="white", font=button_font, width=20, height=2, relief="raised", bd=3
)
start_button.pack(side="left", padx=10)

stop_button = tk.Button(
    button_frame, text="⛔ Stop Surveillance", command=stop_surveillance,
    bg="red", fg="white", font=button_font, width=20, height=2, relief="raised", bd=3
)
stop_button.pack(side="left", padx=10)

view_unknowns_btn = tk.Button(
    button_frame, text="📁 Open Snapshots Folder", command=open_unknown_folder,
    bg="#333", fg="white", font=button_font, width=25, height=2, relief="raised", bd=3
)
view_unknowns_btn.pack(side="left", padx=10)

view_log_btn = tk.Button(
    button_frame, text="📄 Open Log File", command=open_log_file,
    bg="#555", fg="white", font=button_font, width=20, height=2, relief="raised", bd=3
)
view_log_btn.pack(side="left", padx=10)

# ===================================================
# Run Application
# ===================================================
window.mainloop()
if video_capture:
    video_capture.release()
cv2.destroyAllWindows()




