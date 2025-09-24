import os

root = "known_faces"  # path to your known faces folder

total_images = 0
person_count = 0

for person in os.listdir(root):
    person_path = os.path.join(root, person)
    if os.path.isdir(person_path):
        person_count += 1
        count = len([f for f in os.listdir(person_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
        print(f"{person}: {count} images")
        total_images += count

print(f"\nTotal employees: {person_count}")
print(f"TOTAL images across all employees: {total_images}")
