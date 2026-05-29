# Fabric Defect Detection System using YOLOv8
Overview

This project is a real-time Fabric Defect Detection System developed as a Final Year Project (FYP). The system uses the YOLOv8 deep learning model to automatically detect and classify defects in fabric images and live video streams. The project aims to improve quality control in textile industries by reducing manual inspection time and increasing detection accuracy.

The system supports both image upload and live camera feed detection with an interactive dashboard for monitoring defect records and analytics.

Features
Real-time fabric defect detection using YOLOv8
Detection through:
Image upload
Live camera/video feed
Defect classification into:
Stain
Hole
Knot
Line
FastAPI backend for API services
React frontend dashboard
SQLite database integration
Detection history and analytics dashboard
ESP32 camera integration support
Trained on 3000+ fabric images
Detection confidence visualization
Technologies Used
Backend
Python
FastAPI
YOLOv8 (Ultralytics)
OpenCV
SQLite
Frontend
React.js
Axios
Chart.js
Hardware
ESP32 Camera Module
Dataset Information

The model was trained on a custom dataset containing more than 3000 fabric images.

Dataset Distribution
Class	Images
Plain Fabric	1000
Stain Defect	500
Hole Defect	500
Knot Defect	500
Line Defect	500
Model Performance
Metric	Value
Model	YOLOv8
Precision	~80%
Detection Type	Real-Time
System Architecture
ESP32 Camera / Image Upload
            ↓
        FastAPI Backend
            ↓
      YOLOv8 Detection
            ↓
      SQLite Database
            ↓
      React Dashboard
Project Structure
fabric-defect-detection/
│
├── backend/
│   ├── main.py
│   ├── model/
│   ├── database/
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
│
├── sample_images/
├── README.md
└── .gitignore
Installation Guide
Clone Repository
git clone https://github.com/your-username/fabric-defect-detection.git
Backend Setup
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
Frontend Setup
cd frontend
npm install
npm start
API Endpoint Example
POST /predict

Upload a fabric image to receive defect predictions.

Future Improvements
Increase model accuracy with larger datasets
Deploy system on cloud platform
Add multiple camera support
Implement mobile application
Add automated report generation
Applications
Textile Industry Quality Control
Automated Fabric Inspection
Smart Manufacturing Systems
Industrial Automation
Contributors
Syed Zaighum Abbas
License

This project is developed for educational and research purposes.
