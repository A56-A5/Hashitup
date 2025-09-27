import os
import imageio.v3 as iio
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)

def create_timelapse_video(image_paths: list[str], output_path: str, fps: int = 10, crossfade_duration: int = 0):
    """
    Combines a list of image paths into a timelapse video with optional crossfade transitions.

    Args:
        image_paths (list[str]): List of paths to the input images.
        output_path (str): The path where the output video will be saved.
        fps (int): Frames per second for the output video.
        crossfade_duration (int): Duration of crossfade in frames between images.
    """
    if not image_paths:
        logger.warning("No images provided for video generation.")
        return

    frames = []
    try:
        # Load all images and convert to numpy arrays
        loaded_images = [iio.imread(path) for path in image_paths]

        for i in range(len(loaded_images)):
            current_image = loaded_images[i]
            frames.append(current_image)

            if crossfade_duration > 0 and i < len(loaded_images) - 1:
                next_image = loaded_images[i+1]
                for j in range(1, crossfade_duration + 1):
                    alpha = j / (crossfade_duration + 1)
                    blended_frame = (current_image * (1 - alpha) + next_image * alpha).astype(np.uint8)
                    frames.append(blended_frame)

        # Use imageio to create video
        iio.imwrite(output_path, frames, fps=fps, codec='libx264')
        logger.info(f"Timelapse video created at {output_path}")
    except Exception as e:
        logger.error(f"Error creating timelapse video: {e}")