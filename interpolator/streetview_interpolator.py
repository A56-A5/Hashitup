import os
import argparse
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
import cv2
import imageio.v2 as imageio   # 👈 avoids DeprecationWarning

# -----------------------------
# Load FILM model from TF Hub
# -----------------------------
print("⏳ Loading FILM model from TensorFlow Hub...")
film_model = hub.load("https://tfhub.dev/google/film/1")
print("✅ FILM model ready!")

# -----------------------------
# Safe image loader (ensures RGB)
# -----------------------------
def load_image(path):
    """Read image and ensure 3 channels (RGB)."""
    img = imageio.imread(path)
    if img.ndim == 2:  # grayscale → RGB
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    elif img.shape[2] == 4:  # RGBA → RGB
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
    return img

# -----------------------------
# Interpolation function
# -----------------------------
def interpolate_pair(img1, img2, exp=2, pair_idx=0):
    # Resize if shapes mismatch
    if img1.shape != img2.shape:
        img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
        print(f"⚠️ Resized frames to {img2.shape}")

    # Normalize [0,1]
    img1 = img1.astype(np.float32) / 255.0
    img2 = img2.astype(np.float32) / 255.0
    img1 = np.expand_dims(img1, axis=0)
    img2 = np.expand_dims(img2, axis=0)

    # Time steps (exp=2 → 3 in-betweens)
    times = np.linspace(0, 1, num=(2**exp)+1)[1:-1]

    frames = [np.clip(img1[0] * 255.0, 0, 255).astype(np.uint8)]  # first frame
    print(f"➡️ Starting interpolation for pair {pair_idx} with {len(times)} in-betweens...")

    for t_idx, t in enumerate(times, start=1):
        inputs = {
            "time": tf.constant([[t]], dtype=tf.float32),
            "x0": tf.convert_to_tensor(img1),
            "x1": tf.convert_to_tensor(img2),
        }
        pred = film_model(inputs, training=False)
        frame = pred["image"].numpy()[0]
        frame = np.clip(frame * 255.0, 0, 255).astype(np.uint8)
        frames.append(frame)
        print(f"   ✅ Generated intermediate frame {t_idx}/{len(times)} for pair {pair_idx}")

    return frames

# -----------------------------
# Save frames to video
# -----------------------------
def frames_to_video(frames, output_path, fps):
    h, w, _ = frames[0].shape
    writer = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    for idx, f in enumerate(frames, start=1):
        writer.write(cv2.cvtColor(f, cv2.COLOR_RGB2BGR))
        print(f"   🎞️ Written {idx}/{len(frames)} frames to video...")
    writer.release()
    print(f"🎥 Video saved at {output_path}")

# -----------------------------
# Main
# -----------------------------
def main(args):
    frame_files = sorted([f for f in os.listdir(args.input_folder) if f.endswith(".png")])

    # Optional suffix filter (--view)
    if args.view:
        frame_files = [f for f in frame_files if f.endswith(f"_{args.view}.png")]

    if len(frame_files) < 2:
        raise FileNotFoundError("❌ Need at least 2 frames in input folder!")

    all_frames = []
    for i in range(len(frame_files) - 1):
        print(f"\n🔹 Processing pair {i+1}/{len(frame_files)-1}: {frame_files[i]} → {frame_files[i+1]}")
        img1 = load_image(os.path.join(args.input_folder, frame_files[i]))
        img2 = load_image(os.path.join(args.input_folder, frame_files[i + 1]))
        interp_frames = interpolate_pair(img1, img2, exp=args.exp, pair_idx=i+1)
        all_frames.extend(interp_frames)

    # Add the very last frame
    last_img = load_image(os.path.join(args.input_folder, frame_files[-1]))
    all_frames.append(last_img)
    print("✅ Added final frame.")

    os.makedirs("output", exist_ok=True)
    output_path = os.path.join("output", f"streetview_{args.view or 'all'}.mp4")
    frames_to_video(all_frames, output_path, args.fps)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_folder", type=str, default="streetview_frames", help="Folder with frames")
    parser.add_argument("--view", type=str, default="", help="Optional suffix in filenames (e.g. 'front')")
    parser.add_argument("--exp", type=int, default=2, help="Interpolation exponent (exp=2 → 3 in-betweens)")
    parser.add_argument("--fps", type=int, default=30, help="FPS for output video")
    args = parser.parse_args()
    main(args)
