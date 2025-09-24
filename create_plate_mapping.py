import csv

mapping = {
    "DZ17 YXR": "Aindree",
    "G526 JHD": "elon_musk",
    "WOR 516K": "emma_watson",
    "MH 20 BQ 20": "leonardo_dicaprio",
    "CZ17 KOD": "shah_rukh_khan",
    "MH 20 EE 7598": "taylor_swift",
    "LR33 TEE": "Unknown1",
    "15-LK-10898": "Unknown2"
}

with open("plate_owner_mapping.csv", mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["PlateNumber", "OwnerName"])
    for plate, owner in mapping.items():
        writer.writerow([plate, owner])

print("✅ Mapping CSV created as 'plate_owner_mapping.csv'")
