# Satellite Image Predictor and Transformation Video Generator with Pollinations AI

This project leverages Pollinations AI to predict future satellite images based on an initial image and metadata, and to generate transformation videos between two satellite images. The application is built with Flask for the backend and a simple HTML/CSS/JavaScript frontend.

## Features

- **Single Image Prediction**: Upload an initial satellite image and predict its future state.
- **Dual Image Transformation Video**: Upload two satellite images from different years and generate a video showing the transformation between them.
- **Image Upload**: Upload satellite images.
- **Metadata Input**: Provide location name, input year, and target year.
- **AI Prediction**: Utilizes Pollinations AI to generate a sequence of future satellite images or transformation videos.
- **Timelapse Video Generation**: Combines images into a smooth timelapse video with crossfade transitions.
- **Error Handling**: Robust error handling for file uploads, API calls, and video generation.
- **Centralized Configuration & Logging**: Easy management of settings and comprehensive logging.
- **Caching**: Implemented caching for Gemini and interpolation results to improve performance.

## Project Structure

```
.env
README.md
config.py
data/
├── cache/
│   ├── gemini/              # Stores cached Gemini API responses
│   └── interpolation/       # Stores cached interpolated frames
├── output/
│   ├── dual/                # Stores generated transformation videos
│   └── predictions/         # Stores AI-generated predicted images
└── user_uploads/
    ├── dual/                # Stores user-uploaded images for dual transformation
    └── single/              # Stores user-uploaded initial images for single prediction
demo/
├── app/
│   ├── __init__.py          # Flask app factory, configuration loading, and logging setup
│   ├── routes.py            # Flask routes for image processing and video generation
│   ├── utils.py             # Utility functions for AI integration and image processing
│   ├── static/              # Static files (CSS, JS, images)
│   └── templates/           # HTML templates
│       └── index.html
logs/                        # Stores application logs and Pollinations AI interaction logs
requirements.txt
run.py                       # Script to run the Flask application
```

## Setup Instructions (Windows with venv)

Follow these steps to set up and run the project on your Windows machine using a virtual environment.

### 1. Clone the Repository

```bash
git clone <repository_url>
cd frame_interpol
```

### 2. Create a Virtual Environment

It's highly recommended to use a virtual environment to manage project dependencies.

```bash
python -m venv venv
```

### 3. Activate the Virtual Environment

```bash
.\venv\Scripts\activate
```

### 4. Install Dependencies

Install all required Python packages using pip:

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a `.env` file in the root directory of the project and add your API keys:

```
GEMINI_API_KEY='YOUR_GEMINI_AI_API_KEY'
SECRET_KEY='your_super_secret_key_here'
POLLINATIONS_API_KEY='YOUR_POLLINATIONS_API_KEY'
```

Replace `YOUR_GEMINI_AI_API_KEY` and `YOUR_POLLINATIONS_API_KEY` with your actual API keys. The `SECRET_KEY` should be a strong, random string.

### 6. Run the Flask Application

Set the Flask environment variable and run the application:

```bash
$env:FLASK_APP = "run.py"
flask run
```

### 7. Access the Application

Open your web browser and navigate to the address provided in the terminal (usually `http://127.0.0.1:5000/`).

## Usage Workflow

### Single Image Prediction
1. **Upload Image**: On the homepage, select the "Single Image Prediction" tab and upload a satellite image.
2. **Enter Metadata**: Fill in the target year for prediction.
3. **Generate Prediction**: Click "Predict Future". The application will:
    - Upload and save your image.
    - Call AI to predict the future image.
    - Display the generated image on the page.

### Dual Image Transformation Video
1. **Upload Images**: On the homepage, select the "Transformation Video" tab and upload two satellite images.
2. **Enter Metadata**: Fill in the years for each image and a location name.
3. **Generate Video**: Click "Generate Video". The application will:
    - Upload and save your images.
    - Use Gemini AI to generate a descriptive prompt.
    - Interpolate frames between the two images.
    - Call Pollinations AI to generate a transformation video.
    - Display the generated video on the page.

## Logging

All application logs, including API interactions and errors, are stored in the `logs/` directory within the project root.

## Error Handling

The application provides user-friendly messages for:
- Missing input fields.
- Invalid file types or sizes.
- Failures during AI image generation, frame interpolation, or video creation.

Check the `logs/` directory for detailed error information.

## Code Quality

The codebase adheres to PEP8 standards, includes meaningful comments and docstrings, and separates concerns into modular functions and scripts for maintainability.

## Future Improvements (Optional)

- **Asynchronous Processing**: Implement background tasks (e.g., using Celery) for long-running AI predictions and video generation to improve UI responsiveness.
- **Frontend Progress Bar**: A more detailed progress bar to show the status of image generation and video creation.
- **More AI Models**: Integrate with other AI image prediction models for diverse results.
- **User Accounts**: Implement user authentication and personal galleries for uploaded images and generated videos.
- **Advanced Video Options**: Allow users to customize video resolution, frame rates, and transition types.