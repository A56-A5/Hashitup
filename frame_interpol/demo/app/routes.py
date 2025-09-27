import os
import json
from flask import Blueprint, render_template, request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename
from .utils import generate_future_prediction, generate_gemini_prompt, interpolate_frames, generate_pollinations_video

main = Blueprint('main', __name__)

# Cache directories
GEMINI_CACHE_DIR = os.path.join('data', 'cache', 'gemini')
INTERPOLATION_CACHE_DIR = os.path.join('data', 'cache', 'interpolation')

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return jsonify({'error': 'No image part in the request'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected image'}), 400

    if file:
        year = request.form.get('year', type=int)
        if not year:
            return jsonify({'error': 'Year not provided'}), 400

        filename = secure_filename(file.filename)
        upload_folder = os.path.join(current_app.root_path, 'data', 'user_uploads')
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)

        try:
            prediction_image_path = generate_future_prediction(filepath, year)
            return jsonify({'prediction_image_url': f'/outputs/{os.path.basename(prediction_image_path)}'})
        except Exception as e:
            return jsonify({'error': f'Prediction failed: {str(e)}'}), 500

    return jsonify({'error': 'Unknown error'}), 500

@main.route('/transform_video', methods=['POST'])
def transform_video():
    if 'image1' not in request.files or 'image2' not in request.files:
        return jsonify({'error': 'Missing one or both image files'}), 400

    file1 = request.files['image1']
    file2 = request.files['image2']

    if file1.filename == '' or file2.filename == '':
        return jsonify({'error': 'One or both image files are not selected'}), 400

    year1 = request.form.get('year1', type=int)
    year2 = request.form.get('year2', type=int)
    location = request.form.get('location')

    if not all([year1, year2, location]):
        return jsonify({'error': 'Missing year or location metadata'}), 400

    if file1 and file2:
        upload_folder_dual = os.path.join(current_app.root_path, 'data', 'user_uploads', 'dual')
        os.makedirs(upload_folder_dual, exist_ok=True)

        filename1 = secure_filename(file1.filename)
        filename2 = secure_filename(file2.filename)

        filepath1 = os.path.join(upload_folder_dual, filename1)
        filepath2 = os.path.join(upload_folder_dual, filename2)

        file1.save(filepath1)
        file2.save(filepath2)

        try:
            # 1. Gemini Analysis with caching
            gemini_cache_key = f'{location}_{year1}_{year2}_{filename1}_{filename2}.json'
            gemini_cache_path = os.path.join(current_app.root_path, GEMINI_CACHE_DIR, gemini_cache_key)
            os.makedirs(os.path.dirname(gemini_cache_path), exist_ok=True)

            if os.path.exists(gemini_cache_path):
                with open(gemini_cache_path, 'r') as f:
                    gemini_prompt = json.load(f)['prompt']
                print("Gemini prompt loaded from cache.")
            else:
                gemini_prompt = generate_gemini_prompt(filepath1, filepath2, year1, year2, location)
                with open(gemini_cache_path, 'w') as f:
                    json.dump({'prompt': gemini_prompt}, f)
                print("Gemini prompt generated and cached.")

            # 2. Frame Interpolation with caching
            interpolation_cache_key = f'{filename1}_{filename2}'
            interpolated_frames_dir = os.path.join(current_app.root_path, INTERPOLATION_CACHE_DIR, interpolation_cache_key)
            os.makedirs(interpolated_frames_dir, exist_ok=True)

            if not os.listdir(interpolated_frames_dir): # Check if directory is empty
                interpolated_frames_dir = interpolate_frames(filepath1, filepath2)
                print("Frames interpolated and cached.")
            else:
                print("Interpolated frames loaded from cache.")

            # 3. Pollinations Video Generation
            video_path = generate_pollinations_video(interpolated_frames_dir, gemini_prompt)

            return jsonify({'video_url': f'/outputs/dual/{os.path.basename(video_path)}'})

        except Exception as e:
            print(f"Caught exception in transform_video: {e}")
            return jsonify({'error': f'Video transformation failed: {str(e)}'}), 500

    return jsonify({'error': 'Unknown error during video transformation'}), 500

@main.route('/outputs/<path:filename>')
def serve_output(filename):
    # This route will serve files from both single and dual output folders
    single_output_dir = os.path.join(current_app.root_path, 'data', 'output')
    dual_output_dir = os.path.join(current_app.root_path, 'data', 'output', 'dual')

    if filename.startswith('dual/'):
        return send_from_directory(dual_output_dir, filename.replace('dual/', ''))
    else:
        return send_from_directory(single_output_dir, filename)