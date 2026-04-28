# AI-Powered-Digital-Content-Piracy-Detection-System


## 📌 Overview

This project is an end-to-end AI-powered system designed to **detect and prevent unauthorized use of digital media content** (videos/audio) across the internet.

It combines:

* Content Protection (DRM, Watermark, Fingerprinting)
* Internet Crawling
* AI-based Detection (Hybrid Matching)
* Real-time Monitoring Dashboard

---

## 🎯 Problem Statement

Digital sports and media content is widely redistributed without authorization across platforms like YouTube, torrents, and streaming sites.

Our system solves this by:

* Tracking content usage
* Detecting piracy even after modifications
* Providing real-time alerts and risk analysis

---

## 🧠 Key Features

✅ Hybrid AI Detection Engine

* Perceptual Hashing (Exact Matching)
* AI Semantic Matching (Vertex AI inspired)

✅ Real-Time Monitoring Dashboard

* Live piracy detection updates
* Risk categorization (HIGH / MEDIUM / LOW)

✅ Smart Crawling System

* Automatically scans internet platforms

✅ Audio + Video Analysis

* Frame-based fingerprinting
* Audio-based semantic matching

---

## 🏗️ Architecture

```
Content Upload
   ↓
Protection Layer (DRM + Watermark + Fingerprint)
   ↓
Ownership Layer (Blockchain + Feature Vector)
   ↓
Internet Crawling Engine
   ↓
Media Processing (Video + Audio)
   ↓
Hybrid AI Detection Engine
   ↓
Prediction + Decision Engine
   ↓
Real-Time Dashboard
```

---

## ⚙️ Tech Stack

* Python
* FastAPI
* OpenCV
* ImageHash
* yt-dlp
* SpeechRecognition
* Tailwind CSS (Frontend)

---

## 🔥 How It Works

1. Original content is protected using watermark + fingerprint
2. System scans internet for similar content
3. Downloads small clips for analysis
4. Extracts:

   * Visual fingerprints
   * Audio/text features
5. Uses hybrid AI model to detect similarity
6. Outputs:

   * Verdict (PIRACY / SUSPICIOUS / SAFE)
   * Risk Level
   * Recommended Action

---

## 📊 Output Example

```
{
  "url": "...",
  "similarity": 0.82,
  "verdict": "SUSPICIOUS",
  "risk": "MEDIUM",
  "action": "MONITOR"
}
```

---

## 🚀 Getting Started

### 1. Clone Repository

```
git clone https://github.com/your-username/piracy-detection.git
cd piracy-detection
```

### 2. Create Virtual Environment

```
python -m venv venv
venv\Scripts\activate   (Windows)
```

### 3. Install Dependencies

```
pip install -r requirements.txt
```

### 4. Install FFmpeg

Download from: https://ffmpeg.org/download.html
Add to PATH

### 5. Run Backend

```
uvicorn backend.app:app --reload
```

### 6. Open Dashboard

Open:

```
http://127.0.0.1:8000/docs
```

---

## 📡 Real-Time Monitoring

The dashboard automatically:

* Fetches new detection results
* Updates every few seconds
* Displays live piracy alerts

---

## 🧠 Innovation

> “We combine deterministic fingerprinting with AI-based semantic matching to detect piracy even when content is modified.”

---

## 🔮 Future Scope

* Google Vertex AI integration
* Speech-to-Text (real AI)
* Telegram & Torrent crawling
* Automated takedown system
* Global content tracking



## 📜 License

This project is for educational and hackathon purposes.
