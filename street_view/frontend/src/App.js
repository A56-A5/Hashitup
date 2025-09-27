import React, { useState, useEffect } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [image, setImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [videoUrl, setVideoUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImage(file);
      setVideoUrl(null);
      setError("");
      
      // Create preview URL
      const reader = new FileReader();
      reader.onload = (e) => setImagePreview(e.target.result);
      reader.readAsDataURL(file);
    }
  };

  const generateVideo = async () => {
    if (!image) return setError("Upload a Street View image first!");

    const formData = new FormData();
    formData.append("image", image);

    setLoading(true);
    setError("");

    try {
      const res = await axios.post("/api/generate-video", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      
      if (res.data.success) {
        // Handle HuggingFace response - either videoFile or content
        if (res.data.videoFile) {
          setVideoUrl(`/api/video/${res.data.videoFile}`);
        } else if (res.data.content) {
          setVideoUrl(res.data.content);
        } else {
          setVideoUrl("Video generated successfully!");
        }
        setLoading(false);
      } else {
        setError("Video generation failed");
        setLoading(false);
      }
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.details || "Failed to generate video");
      setLoading(false);
    }
  };

  // No need for polling since we're using synchronous API

  return (
    <div className="app-container">
      <div className="card">
        <div className="header">
          <h1 className="title">Street View → Smooth Dashcam Video</h1>
          <p className="subtitle">Transform your Street View images into realistic dashcam-style videos using HuggingFace SVD</p>
        </div>

        <div className="upload-section">
          <div className="file-input-container">
            <input 
              type="file" 
              id="image-upload"
              accept="image/*" 
              onChange={handleUpload}
              className="file-input"
            />
            <label htmlFor="image-upload" className="file-input-label">
              <div className="upload-icon">📷</div>
              <div className="upload-text">
                {image ? "Change Image" : "Choose Street View Image"}
              </div>
              <div className="upload-hint">PNG, JPG, or JPEG files</div>
            </label>
          </div>

          {imagePreview && (
            <div className="image-preview">
              <img src={imagePreview} alt="Preview" />
              <div className="image-info">
                <span className="image-name">{image.name}</span>
                <span className="image-size">
                  {(image.size / 1024 / 1024).toFixed(2)} MB
                </span>
              </div>
            </div>
          )}
        </div>

        <button 
          onClick={generateVideo} 
          disabled={loading || !image}
          className="generate-button"
        >
          {loading ? (
            <>
              <div className="button-spinner"></div>
              Generating... (5 min approx)
            </>
          ) : (
            "Generate Video"
          )}
        </button>

        {error && <div className="error-message">{error}</div>}

        {loading && !videoUrl && (
          <div className="loading-container">
            <div className="loading-spinner"></div>
            <div className="loading-text">
              <h3>Processing your video...</h3>
              <p>This may take up to 5 minutes. Please don't close this page.</p>
            </div>
          </div>
        )}

        {videoUrl && (
          <div className="video-container">
            <h2>Generated Video</h2>
            <div className="content-wrapper">
              {videoUrl.startsWith('http') ? (
                <div className="video-player">
                  <video 
                    controls 
                    style={{ width: '100%', maxWidth: '600px', borderRadius: '10px' }}
                    src={videoUrl}
                  >
                    Your browser does not support the video tag.
                  </video>
                  <div className="video-info">
                    <p><strong>Video URL:</strong> <a href={videoUrl} target="_blank" rel="noopener noreferrer">{videoUrl}</a></p>
                  </div>
                </div>
              ) : (
                <div className="generated-content">
                  <h3>AI Response:</h3>
                  <p>{videoUrl}</p>
                </div>
              )}
            </div>
            <div className="content-actions">
              <button 
                onClick={() => navigator.clipboard.writeText(videoUrl)}
                className="copy-button"
              >
                Copy URL to Clipboard
              </button>
              {videoUrl.startsWith('http') && (
                <button 
                  onClick={() => window.open(videoUrl, '_blank')}
                  className="copy-button"
                  style={{ marginLeft: '10px' }}
                >
                  Open Video
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
