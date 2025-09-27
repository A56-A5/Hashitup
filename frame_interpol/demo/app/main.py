import os
import logging
from flask import Blueprint, render_template, request, redirect, url_for, send_file, current_app, flash, send_from_directory
from werkzeug.utils import secure_filename

from scripts.pollinations_orchestrator import orchestrate_pollinations_predictions
from scripts.video_generator import create_timelapse_video

bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

def allowed_file(filename: str) -> bool:
    """
    Checks if the uploaded file has an allowed extension.

    Args:
        filename (str): The name of the file to check.

    Returns:
        bool: True if the file extension is allowed, False otherwise.
    """
    allowed = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed

@bp.route('/images/<path:filename>')
def serve_image(filename):
    """
    Serves images from the user uploads or predictions directory.
    """
    # Determine if the image is from user uploads or predictions
    base_filename = os.path.basename(filename)
    user_upload_dir = current_app.config['USER_UPLOADS_DIR']
    predictions_dir = current_app.config['PREDICTIONS_DIR']

    user_upload_path = os.path.join(user_upload_dir, base_filename)
    prediction_path = os.path.join(predictions_dir, base_filename)

    logger.info(f"serve_image - user_upload_dir: {user_upload_dir}")
    logger.info(f"serve_image - predictions_dir: {predictions_dir}")
    logger.info(f"serve_image - user_upload_path: {user_upload_path}")
    logger.info(f"serve_image - prediction_path: {prediction_path}")

    if os.path.exists(user_upload_path):
        logger.info(f"Serving uploaded image: {user_upload_path}")
        try:
            return send_file(user_upload_path)
        except Exception as e:
            logger.error(f"Error serving uploaded image {user_upload_path}: {e}")
            return "Error serving image", 500
    elif os.path.exists(prediction_path):
        logger.info(f"Serving predicted image: {prediction_path}")
        try:
            return send_file(prediction_path)
        except Exception as e:
            logger.error(f"Error serving predicted image {prediction_path}: {e}")
            return "Error serving image", 500
    else:
        logger.error(f"Image not found: {filename} in {user_upload_dir} or {predictions_dir}")
        return "Image not found", 404


@bp.route('/videos/<path:filename>')
def serve_video(filename):
    """
    Serves video files from the output directory.
    """
    output_dir = current_app.config['OUTPUT_VIDEO_DIR']
    base_filename = os.path.basename(filename)
    video_path = os.path.join(output_dir, base_filename)

    logger.info(f"serve_video - output_dir: {output_dir}")
    logger.info(f"serve_video - video_path: {video_path}")

    if os.path.exists(video_path):
        logger.info(f"Serving video: {video_path}")
        try:
            return send_file(video_path, mimetype='video/mp4')
        except Exception as e:
            logger.error(f"Error serving video {video_path}: {e}")
            return "Error serving video", 500
    else:
        logger.error(f"Video not found: {video_path}")
        return "Video not found", 404


@bp.route('/', methods=['GET'])
def index():
    """
    Renders the home page of the application, focusing on user-uploaded images.
    """
    return render_template('index.html')


@bp.route('/process', methods=['POST'])
def process_images():
    """
    Handles the form submission for image processing with a single user-uploaded image and new metadata.

    Validates input, saves the uploaded file, orchestrates Pollinations AI predictions,
    generates a timelapse video, and renders the results on the index page.

    Returns:
        Response: A Flask response object, either rendering the index page with results
                  or redirecting with error messages.
    """
    try:
        # Extract new metadata
        location_name = request.form.get('location_name', '')
        input_year = request.form.get('input_year', type=int)
        target_year = request.form.get('target_year', type=int)
        interval = request.form.get('interval', type=int)

        if not all([location_name, input_year, target_year, interval]):
            flash("Location name, input year, target year, and interval are required.", 'error')
            return redirect(url_for('main.index'))

        if 'file' not in request.files:
            flash("An image file is required.", 'error')
            return redirect(url_for('main.index'))

        file = request.files['file']

        if file.filename == '':
            flash("Please select an image file.", 'error')
            return redirect(url_for('main.index'))

        # Input validation
        if not allowed_file(file.filename):
            flash("Invalid file type. Please upload a JPG, PNG, JPEG, or GIF image.", 'error')
            return redirect(url_for('main.index'))

        if target_year <= input_year:
            flash("Target year must be greater than input year.", 'error')
            return redirect(url_for('main.index'))

        # Check file size before saving
        file.seek(0)  # Reset file pointer to the beginning
        if len(file.read()) > current_app.config['MAX_CONTENT_LENGTH']:
            flash(f"File size exceeds the maximum limit of {current_app.config['MAX_CONTENT_LENGTH'] / (1024 * 1024):.0f} MB.", 'error')
            return redirect(url_for('main.index'))
        file.seek(0) # Reset file pointer after reading for saving

        # Securely save the uploaded file
        filename = secure_filename(file.filename)
        uploads_dir = os.path.abspath(current_app.config['USER_UPLOADS_DIR'])
        filepath = os.path.join(uploads_dir, filename)
        file.save(filepath)
        logger.info(f"Uploaded file saved to {filepath}")

        # Pollinations AI orchestration and iterative image generation
        predictions_dir = os.path.abspath(current_app.config['PREDICTIONS_DIR'])
        logs_dir = os.path.abspath(current_app.config['LOGS_DIR'])
        generated_image_paths = orchestrate_pollinations_predictions(
            initial_image_path=filepath,
            location_name=location_name,
            input_year=input_year,
            target_year=target_year,
            interval=interval,
            predictions_dir=predictions_dir,
            logs_dir=logs_dir
        )

        # Video generation
        video_url = None
        if generated_image_paths:
            logger.info(f"Generated image paths for video: {generated_image_paths}")
            video_output_dir = os.path.abspath(current_app.config['OUTPUT_VIDEO_DIR'])
            video_filename = f"timelapse_{os.path.basename(filepath).split('.')[0]}.mp4"
            video_output_path = os.path.join(video_output_dir, video_filename)
            logger.info(f"Attempting to create video at: {video_output_path}")
            try:
                create_timelapse_video(generated_image_paths, video_output_path, fps=current_app.config['VIDEO_FPS'])
                # Only set video_url if the file actually exists
                if os.path.exists(video_output_path):
                    video_url = url_for('main.serve_video', filename=video_filename)
                    flash("Video generated successfully!", 'success')
                    logger.info(f"Video successfully generated and URL created: {video_url}")
                else:
                    logger.error(f"Video file not found after generation attempt: {video_output_path}")
                    flash("Failed to generate video file.", 'error')
            except Exception as video_e:
                logger.error(f"Error during video creation: {video_e}")
                flash(f"Error generating video: {video_e}", 'error')
        else:
            flash("Failed to generate images or video.", 'error')
            logger.warning("No generated image paths to create video.")

        return render_template(
            'index.html',
            uploaded_image=filename,
            generated_images=[os.path.basename(p) for p in generated_image_paths[1:]] if generated_image_paths else [],
            video_url=video_url
        )
    except Exception as e:
        logger.error(f"Error during image processing: {e}")
        flash(f"An unexpected error occurred: {e}", 'error')
        return redirect(url_for('main.index'))