import shutil
import os

base_dir = r"c:\Users\shaikh shahab\OneDrive\Desktop\Trainer_personal_details\Atmayantra\Atmayantra"
target_dir = os.path.join(base_dir, "doctors_profile")

apps_to_move = [
    "doctor_personal_details",
    "doctor_certification",
    "doctor_documents",
    "doctor_bank_details"
]

for app in apps_to_move:
    src = os.path.join(base_dir, app)
    dst = os.path.join(target_dir, app)
    if os.path.exists(src) and not os.path.exists(dst):
        shutil.move(src, dst)
        print(f"Moved {src} to {dst}")
    else:
        print(f"Skipped {src} (doesn't exist or already at destination)")
