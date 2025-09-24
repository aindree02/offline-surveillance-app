roject Overview:-

This project implements a Smart Surveillance System that integrates facial recognition and automatic number plate recognition (ANPR) for real-time dual authentication. It combines open-source tools such as OpenCV, face_recognition, EasyOCR, and PyQt5 into an offline, GUI-based application. The system is designed to be user-friendly for non-technical staff, scalable, and deployable without reliance on cloud services.

                                           *Overview*

This project implements a Smart Surveillance System that combines facial recognition and number plate recognition into one unified real-time application. It provides dual authentication at access points (e.g., campuses, offices, residential complexes) using open-source tools and a GUI for non-technical users.

The system is designed to:
Recognize known and unknown faces in real time.
Detect and match vehicle number plates against registered users.
Provide an admin GUI for registration, monitoring, and log review.
Work offline, packaged as a standalone application for usability and scalability.



Features:-

Facial Recognition using face_recognition (dlib + HOG/SVM pipeline).
Number Plate Recognition (NPR) using EasyOCR with regex and fuzzy matching.
Admin GUI (PyQt5) for:
Registering employees and vehicles.
Uploading multiple images per user.
Live webcam-based detection.
Viewing logs (CSV format).
Structured Logging of known and unknown faces/plates for auditing.
Standalone Deployment using PyInstaller (.app for macOS, .exe for Windows).


Project Structure:-

SmartSurveillance_Project/
│── known_faces/                # Registered face images (per user folder)
│── unknown_faces/              # Auto-saved unrecognized faces
│── test_faces/known/           # Test set of known faces
│── test_faces/unknown/         # Test set of unknown faces
│── test_plates/known/          # Test set of known plates
│── test_plates/unknown/        # Test set of unknown plates
│── logs/                       # Contains CSV logs of detections
│   ├── known_faces_log.csv
│   ├── unknown_faces_log.csv
│   ├── known_plate_log.csv
│   ├── unknown_plate_log.csv
│── encodings.pkl               # Serialized facial encodings
│── plate_owner_mapping.csv     # Maps vehicle plates → employees
│── admin_gui.py                # Main GUI application
│── enhanced_gui.py             # Extended GUI with advanced features
│── generate_encodings.py       # Generates face encodings from images
│── test_face_accuracy.py       # Evaluates face recognition module
│── test_plate_accuracy.py      # Evaluates number plate recognition
│── Number_Plate_OCR.py         # Core OCR logic for number plates
│── download_more_images.py     # Script to augment dataset
│── download_unknown_faces.py   # Captures unknown faces automatically

                      *Installation*
python -m venv venv
source venv/bin/activate   # On macOS/Linux
venv\Scripts\activate      # On Windows

Install all required packages:
pip install -r requirements.txt

This will automatically install OpenCV, dlib, face_recognition, EasyOCR, PyQt5, and other libraries needed to run the Smart Surveillance System.



                      *Usage*
*Run the Admin GUI*
python admin_gui.py:-Register new users and vehicles.
                     Upload multiple face images.
                     Link number plates.
                     Start live monitoring.
                     Evaluate Face Recognition

*Evaluate Face Recognition*
python test_face_accuracy.py

*Evaluate Number Plate Recognition*
python test_plate_accuracy.py


*Evaluation Results*

Facial Recognition Accuracy: ~89.14% overall
Number Plate Recognition Accuracy: ~83.33% overall
Confusion matrices, precision, recall, and F1-scores confirm strong recognition with reliable rejection of unknowns.




*Future Work*

Automated license plate localization (YOLO/Deep Learning).
Improved face alignment & low-light handling.
Multi-face tracking in crowded scenes.
Cloud integration for remote access.
Cross-platform packaging improvements.
