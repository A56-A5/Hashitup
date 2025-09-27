// server.js
import express from "express";
import multer from "multer";
import axios from "axios";
import fs from "fs";
import path from "path";
import dotenv from "dotenv";
import cors from "cors";

dotenv.config();

const app = express();
const upload = multer({ dest: "uploads/" });

// ---- CONFIG ----
const HF_API_KEY = process.env.HF_API_KEY || "your_key_here";
const FRONTEND_URL = process.env.FRONTEND_URL || "http://localhost:3000";

console.log("Configuration:");
console.log("- HuggingFace API Key:", HF_API_KEY ? "✅ Present" : "❌ Missing");
console.log("- Frontend URL:", FRONTEND_URL);

// ---- MIDDLEWARE ----
app.use(cors({ origin: FRONTEND_URL, credentials: true }));
app.use(express.json({ limit: "50mb" }));
app.use(express.urlencoded({ limit: "50mb", extended: true }));

// ---- HEALTH CHECK ----
app.get("/api/health", async (req, res) => {
  try {
    res.json({
      status: "ok",
      provider: "HuggingFace",
      apiKeyPresent: !!HF_API_KEY,
      model: "stabilityai/stable-video-diffusion-img2vid",
    });
  } catch (err) {
    res.status(500).json({ status: "error", error: err.message });
  }
});

// ---- GENERATE VIDEO (HuggingFace SVD) ----
app.post("/api/generate-video", upload.single("image"), async (req, res) => {
  let uploadedFile = null;
  try {
    if (!req.file) {
      return res.status(400).json({ success: false, error: "No image uploaded" });
    }

    uploadedFile = req.file.path;
    const prompt =
      (req.body.prompt || "").trim() ||
      "Generate a smooth dashcam-style video with realistic scenery, based on this Street View image.";

    console.log("🎬 Generating video with HuggingFace SVD:", req.file.originalname);

    const HF_API_URL =
      "https://api-inference.huggingface.co/models/stabilityai/stable-video-diffusion-img2vid";
    const HF_TOKEN = process.env.HF_API_KEY || "y9ur_key_here";

    if (!HF_TOKEN) {
      throw new Error("Missing HF_API_KEY in environment variables");
    }

    // Read image as raw binary
    const imageBuffer = fs.readFileSync(uploadedFile);

    // Send directly as binary (multipart/form-data is optional, but raw works better here)
    const response = await axios.post(HF_API_URL, imageBuffer, {
      headers: {
        Authorization: `Bearer ${HF_TOKEN}`,
        "Content-Type": "application/octet-stream",
      },
      responseType: "arraybuffer", // HuggingFace returns raw video bytes
      timeout: 300000,
    });

    // Save output video
    const outPath = `output_${Date.now()}.mp4`;
    fs.writeFileSync(outPath, response.data);

    res.json({ success: true, videoFile: outPath });
  } catch (err) {
    console.error("❌ generate-video error:", err.response?.data || err.message);
    res.status(500).json({
      success: false,
      error: "Video generation failed",
      details: err.response?.data || err.message,
    });
  } finally {
    if (uploadedFile && fs.existsSync(uploadedFile)) fs.unlinkSync(uploadedFile);
  }
});

// ---- SERVE GENERATED VIDEOS ----
app.get("/api/video/:filename", (req, res) => {
  const filename = req.params.filename;
  const videoPath = path.join(process.cwd(), filename);
  
  if (fs.existsSync(videoPath)) {
    res.sendFile(videoPath);
  } else {
    res.status(404).json({ error: "Video file not found" });
  }
});

// ---- ERROR HANDLER ----
app.use((err, req, res, next) => {
  console.error("Unhandled error:", err);
  res.status(500).json({ success: false, error: "Internal server error", details: err.message });
});

// ---- START ----
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`🚀 Server running on http://localhost:${PORT}`);
  console.log("Endpoints:");
  console.log("  GET  /api/health");
  console.log("  POST /api/generate-video (multipart form-data: image=file)");
  console.log("  GET  /api/video/:filename (serve generated videos)");
  console.log("Using HuggingFace Stable Video Diffusion for video generation");
});
