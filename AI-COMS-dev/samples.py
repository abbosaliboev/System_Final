import os
import shutil
import random

# Input paths
adl_path = r"C:\Users\dalab\Desktop\azimjaan21\SafeFactory System\Datasets\GMDCSA24\Subject 1\ADL"
fall_path = r"C:\Users\dalab\Desktop\azimjaan21\SafeFactory System\Datasets\GMDCSA24\Subject 1\Fall"

# Output base folder
output_base = r"C:\Users\dalab\Desktop\azimjaan21\SafeFactory System\Datasets\GMDCSA24\samples"

# List video files
adl_videos = [f for f in os.listdir(adl_path) if f.endswith(('.mp4', '.avi', '.mkv'))]
fall_videos = [f for f in os.listdir(fall_path) if f.endswith(('.mp4', '.avi', '.mkv'))]

# Shuffle
random.shuffle(adl_videos)
random.shuffle(fall_videos)

# Take 51 from each to form 3 groups of 17
adl_videos = adl_videos[:51]
fall_videos = fall_videos[:51]

adl_samples = [adl_videos[i * 17: (i + 1) * 17] for i in range(3)]
fall_samples = [fall_videos[i * 17: (i + 1) * 17] for i in range(3)]

# Create sample folders with ADL and Fall subfolders
for i in range(3):
    sample_name = f"sample{i+1}"
    adl_out = os.path.join(output_base, sample_name, "ADL")
    fall_out = os.path.join(output_base, sample_name, "Fall")

    os.makedirs(adl_out, exist_ok=True)
    os.makedirs(fall_out, exist_ok=True)

    # Copy ADL videos
    for vid in adl_samples[i]:
        src = os.path.join(adl_path, vid)
        dst = os.path.join(adl_out, vid)
        shutil.copy2(src, dst)

    # Copy Fall videos
    for vid in fall_samples[i]:
        src = os.path.join(fall_path, vid)
        dst = os.path.join(fall_out, vid)
        shutil.copy2(src, dst)

print("✅ Done: Videos split into sample1/sample2/sample3 with ADL and Fall subfolders.")
