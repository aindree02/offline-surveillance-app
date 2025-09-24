import sys
import os
import shutil
import csv
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QHBoxLayout, QInputDialog
)

# ========= Path Compatibility for PyInstaller ========= #
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS  # Temporary folder created by PyInstaller
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

KNOWN_FACES_DIR = os.path.join(base_path, "known_faces")
PLATE_CSV = os.path.join(base_path, "plate_owner_mapping.csv")

# ========= GUI CLASS ========= #
class AdminGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Admin Panel - Manage Employees")
        self.setGeometry(300, 200, 600, 450)

        self.layout = QVBoxLayout()

        # ---- Search Section ---- #
        search_label = QLabel("Search Employee by Name:")
        self.layout.addWidget(search_label)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_btn = QPushButton("🔍 Search")
        self.search_btn.clicked.connect(self.search_employee)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)
        self.layout.addLayout(search_layout)

        self.search_result_label = QLabel("")
        self.layout.addWidget(self.search_result_label)

        self.add_photos_btn = QPushButton("📷 Add More Photos")
        self.add_photos_btn.clicked.connect(self.add_more_photos)
        self.add_photos_btn.hide()

        self.update_plate_btn = QPushButton("🔄 Update Plate Number")
        self.update_plate_btn.clicked.connect(self.update_plate_number)
        self.update_plate_btn.hide()

        self.delete_btn = QPushButton("🗑 Delete Employee")
        self.delete_btn.clicked.connect(self.delete_employee)
        self.delete_btn.hide()

        self.layout.addWidget(self.add_photos_btn)
        self.layout.addWidget(self.update_plate_btn)
        self.layout.addWidget(self.delete_btn)

        # ---- Add New Employee ---- #
        self.layout.addWidget(QLabel("Employee Name:"))
        self.name_input = QLineEdit()
        self.layout.addWidget(self.name_input)

        self.layout.addWidget(QLabel("Car Plate Number (optional):"))
        self.plate_input = QLineEdit()
        self.layout.addWidget(self.plate_input)

        self.select_btn = QPushButton("📷 Select Face Images")
        self.select_btn.clicked.connect(self.select_images)
        self.layout.addWidget(self.select_btn)

        self.save_btn = QPushButton("✅ Save / Add New Employee")
        self.save_btn.clicked.connect(self.save_employee)
        self.layout.addWidget(self.save_btn)

        self.setLayout(self.layout)

        self.selected_images = []
        self.current_search_name = None

    def select_images(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.ExistingFiles)
        dialog.setNameFilter("Image Files (*.jpg *.jpeg *.png)")
        dialog.setViewMode(QFileDialog.Detail)

        if dialog.exec_():
            files = dialog.selectedFiles()
            if files:
                self.selected_images = files
                QMessageBox.information(self, "Images Selected", f"{len(files)} images selected.")

    def save_employee(self):
        emp_name = self.name_input.text().strip()
        plate_number = self.plate_input.text().strip().upper()

        if not emp_name:
            QMessageBox.critical(self, "Error", "Please enter the employee name!")
            return

        if not self.selected_images and not plate_number:
            QMessageBox.critical(self, "Error", "Select face images or enter a plate number!")
            return

        os.makedirs(KNOWN_FACES_DIR, exist_ok=True)
        emp_folder = os.path.join(KNOWN_FACES_DIR, emp_name)
        os.makedirs(emp_folder, exist_ok=True)

        saved_images_count = 0
        for img_path in self.selected_images:
            shutil.copy(img_path, emp_folder)
            saved_images_count += 1

        if plate_number:
            csv_exists = os.path.exists(PLATE_CSV)
            with open(PLATE_CSV, mode="a", newline="") as file:
                writer = csv.writer(file)
                if not csv_exists:
                    writer.writerow(["PlateNumber", "OwnerName"])
                writer.writerow([plate_number, emp_name])

        msg = f"Employee {emp_name} added successfully.\nImages: {saved_images_count}"
        if plate_number:
            msg += f"\nPlate Number: {plate_number}"
        QMessageBox.information(self, "Saved", msg)

        self.name_input.clear()
        self.plate_input.clear()
        self.selected_images.clear()

    def search_employee(self):
        name = self.search_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a name.")
            return

        emp_folder = os.path.join(KNOWN_FACES_DIR, name)
        if not os.path.exists(emp_folder):
            self.search_result_label.setText(f"❌ No record found for {name}")
            self.add_photos_btn.hide()
            self.update_plate_btn.hide()
            self.delete_btn.hide()
            return

        photo_count = len([f for f in os.listdir(emp_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])

        plate_number = "Not Assigned"
        if os.path.exists(PLATE_CSV):
            with open(PLATE_CSV, "r") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row["OwnerName"].strip().lower() == name.lower():
                        plate_number = row["PlateNumber"]
                        break

        self.search_result_label.setText(
            f"✅ Name: {name}\n✅ Photos: {photo_count}\n✅ Plate: {plate_number}"
        )

        self.current_search_name = name
        self.add_photos_btn.show()
        self.update_plate_btn.show()
        self.delete_btn.show()

    def add_more_photos(self):
        if not self.current_search_name:
            return
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.ExistingFiles)
        dialog.setNameFilter("Image Files (*.jpg *.jpeg *.png)")

        if dialog.exec_():
            files = dialog.selectedFiles()
            emp_folder = os.path.join(KNOWN_FACES_DIR, self.current_search_name)
            for img_path in files:
                shutil.copy(img_path, emp_folder)
            QMessageBox.information(self, "Photos Added", f"Added {len(files)} photos.")

    def update_plate_number(self):
        if not self.current_search_name:
            return
        new_plate, ok = QInputDialog.getText(self, "Update Plate", "Enter new plate number:")
        if not ok or not new_plate.strip():
            return

        new_plate = new_plate.strip().upper()
        rows = []
        if os.path.exists(PLATE_CSV):
            with open(PLATE_CSV, "r") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row["OwnerName"].strip().lower() == self.current_search_name.lower():
                        row["PlateNumber"] = new_plate
                    rows.append(row)

        with open(PLATE_CSV, "w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=["PlateNumber", "OwnerName"])
            writer.writeheader()
            for row in rows:
                writer.writerow(row)

        QMessageBox.information(self, "Updated", f"Plate updated to {new_plate}")

    def delete_employee(self):
        if not self.current_search_name:
            return

        confirm = QMessageBox.question(
            self, "Confirm Delete", f"Delete {self.current_search_name}?", QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        emp_folder = os.path.join(KNOWN_FACES_DIR, self.current_search_name)
        if os.path.exists(emp_folder):
            shutil.rmtree(emp_folder)

        if os.path.exists(PLATE_CSV):
            rows = []
            with open(PLATE_CSV, "r") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row["OwnerName"].strip().lower() != self.current_search_name.lower():
                        rows.append(row)
            with open(PLATE_CSV, "w", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=["PlateNumber", "OwnerName"])
                writer.writeheader()
                for row in rows:
                    writer.writerow(row)

        QMessageBox.information(self, "Deleted", f"Employee {self.current_search_name} deleted.")
        self.search_result_label.setText("")
        self.add_photos_btn.hide()
        self.update_plate_btn.hide()
        self.delete_btn.hide()
        self.current_search_name = None

# ========= Launch App ========= #
def run_admin_gui():
    app = QApplication(sys.argv)
    window = AdminGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run_admin_gui()
