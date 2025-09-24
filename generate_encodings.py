import cv2
import face_recognition
import numpy as np
import os
from datetime import datetime
import csv
import tkinter as tk
from PIL import Image, ImageTk
import threading
import pickle

# Directories
KNOWN_FACES_DIR = "known_faces"
UNKNOWN_DIR = "Unknown_faces"
LOG_FILE = "unknown_faces_log.csv"
ENCODING_FILE = "encodings.pkl"

# Load known encodings from pickle file
if not os.path.exists(ENCODING_FILE):
    raise FileNotFoundError("encodings.pkl not found! Please generate it first.")

with open(ENCODING_FILE, "rb") as f:
    known_encodings, known_names = pickle.load(f)

# Debug: Show names loaded from pickle
print(f"[INFO] Loaded {len(known_encodings)} known encodings from file.")
print("[DEBUG] Known Names in encodings.pkl:", known_names)

# Save unknown face only once per session using face encoding fingerprint
saved_faces = []

# Ensure unknown_faces folder exists
os.makedirs(UNKNOWN_DIR, exist_ok=True)

# Create CSV log file with header if not exists
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Date", "Time", "Saved Image Name"])

# Initialize webcam
video_capture = None
running = False

# GUI setup
window = tk.Tk()
window.title("Smart Surveillance System")
window.geometry("800x600")
window.configure(bg="#1e1e1e")

video_label = tk.Label(window, bg="#1e1e1e")
video_label.pack(pady=10)

status_label = tk.Label(window, text="Status: Idle", font=("Helvetica", 12), fg="white", bg="#1e1e1e")
status_label.pack(pady=5)

def start_surveillance():
    global video_capture, running
    if not running:
        video_capture = cv2.VideoCapture(0)
        running = True
        status_label.config(text="Status: Monitoring", fg="lightgreen")
        update_frame()

def stop_surveillance():
    global video_capture, running
    if running:
        running = False
        if video_capture:
            video_capture.release()
        video_label.config(image='')
        status_label.config(text="Status: Stopped", fg="orange")

def update_frame():
    global video_capture, running
    if not running:
        return

    ret, frame = video_capture.read()
    if not ret:
        return

    # Resize frame for faster processing
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
            matched_name = known_names[best_match_index].strip()
            name = matched_name

        # Debug print of recognition
        print(f"[INFO] Detected and recognized: {name}")

        if name.lower() == "unknown":
            # Use cosine similarity to reduce duplicate saves
            is_new = True
            for saved in saved_faces:
                similarity = np.dot(face_encoding, saved) / (np.linalg.norm(face_encoding) * np.linalg.norm(saved))
                if similarity > 0.97:
                    is_new = False
                    break

            if is_new:
                saved_faces.append(face_encoding)
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
                print(f"[INFO] Unknown face saved: {filename}")

        # Draw rectangle and name
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(frame, name, (left, top - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(img)
    imgtk = ImageTk.PhotoImage(image=img)
    video_label.imgtk = imgtk
    video_label.configure(image=imgtk)
    window.after(10, update_frame)

# Buttons
button_frame = tk.Frame(window, bg="#1e1e1e")
button_frame.pack(pady=15)

start_button = tk.Button(button_frame, text="▶ Start Surveillance", command=start_surveillance, bg="green", fg="white", font=("Helvetica", 12), width=20)
start_button.pack(side="left", padx=10)

stop_button = tk.Button(button_frame, text="⛔ Stop Surveillance", command=stop_surveillance, bg="red", fg="white", font=("Helvetica", 12), width=20)
stop_button.pack(side="right", padx=10)

# Start GUI
window.mainloop()

# Cleanup
if video_capture:
    video_capture.release()
cv2.destroyAllWindows()


