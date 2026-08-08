# AI Based Fabric Defects Detection System

> Final Year Project (FYP) — real-time fabric defect detection using YOLOv8 with image-upload and live-stream (ESP32-CAM) modes, backed by a FastAPI service and a React frontend.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Defect Classes](#defect-classes)
- [Quick Start](#quick-start)
- [Backend (FastAPI)](#backend-fastapi)
  - [Configuration](#configuration)
  - [Running the Backend](#running-the-backend)
  - [Detector Service](#detector-service)
  - [Live Stream Manager](#live-stream-manager)
  - [API Reference](#api-reference)
- [Frontend (React + Vite)](#frontend-react--vite)
  - [Configuration](#frontend-configuration)
  - [Running the Frontend](#running-the-frontend)
  - [Routing](#routing)
  - [Services Layer](#services-layer)
- [Data Models](#data-models)
- [Authentication](#authentication)
- [Environment Variables](#environment-variables)
- [Model Files](#model-files)
- [Notes & Caveats](#notes--caveats)

---

## Overview

This system detects common fabric defects (hole, knot, line, stain) on a moving production line. It uses two Ultralytics YOLOv8 models:

- `nano.pt` — fast, lower accuracy
- `medium.pt` — more accurate, slower

Two operational modes are supported:

1. **Image Upload** — operator uploads a still image; the API returns bounding boxes and a visualized result.
2. **Live Stream** — operator connects to an ESP32-CAM MJPEG stream (or a system camera / local video file); frames are continuously inferred, defects are saved into a "pending" table, and the operator can later accept them onto the dashboard.

A per-user SQLite database tracks users, confirmed defects, and pending defects.

---

## Features

- **User auth** — JWT bearer tokens with bcrypt password hashing
- **Image detection** — single-image upload with annotated result image
- **Live detection** — ESP32-CAM / laptop webcam / local video with frame polling and FPS display
- **Pending defects workflow** — auto-save detection → manual accept/reject → confirm to dashboard
- **Dashboard charts** — defect type distribution, daily trend, confidence histogram (Chart.js)
- **Per-user filtering** — every defect record is scoped to the authenticated user
- **Auto-fallback** — if ESP32-CAM stream fails repeatedly, the manager falls back to a local video file (e.g. `fabric.mp4`, `video23.mp4`, `faults.mp4`)
- **Responsive UI** — Tailwind CSS with `btn-primary`, `btn-secondary`, `btn-danger`, `card`, `stat-card`, `input-field` utility classes

---

## Tech Stack

| Layer    | Technology |
|----------|------------|
| Backend  | FastAPI, Uvicorn, SQLAlchemy 2.x, SQLite, Ultralytics YOLOv8, OpenCV, NumPy, Pillow, python-jose JWT, passlib bcrypt |
| Frontend | React 18, Vite 5, React Router v6, Axios, Tailwind CSS 3, Chart.js 4, react-chartjs-2 |
| ML       | YOLOv8 (Ultralytics) — `nano.pt`, `medium.pt` |
| Camera   | ESP32-CAM (MJPEG over HTTP) — default `http://172.22.115.216:81/stream` |
| DB       | Single SQLite file at `backend/fabric.db` |

---

## Project Structure

```
FYP Final/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app + CORS + router includes
│   │   ├── config.py               # Settings (DB URL, JWT, model paths, ESP32 URL, class metadata)
│   │   ├── database.py             # SQLAlchemy engine + SessionLocal + init_db
│   │   ├── deps.py                 # get_current_user dependency (JWT bearer)
│   │   ├── __init__.py
│   │   ├── models/
│   │   │   ├── base.py             # SQLAlchemy declarative Base
│   │   │   ├── user.py             # User ORM
│   │   │   ├── defect.py           # Defect ORM (confirmed defects)
│   │   │   └── pending_defect.py   # PendingDefect ORM
│   │   ├── schemas/
│   │   │   ├── user.py             # Pydantic: UserCreate/Login/Response/Token
│   │   │   └── defect.py           # Pydantic: Defect* / DashboardStats / ChartData / Pending*
│   │   ├── routers/
│   │   │   ├── auth.py             # /api/auth/*
│   │   │   ├── images.py           # /api/images/*
│   │   │   ├── live.py             # /api/live/*
│   │   │   └── dashboard.py        # /api/dashboard/*
│   │   ├── services/
│   │   │   ├── detector.py         # Singleton YOLO wrapper (image inference + bbox drawing)
│   │   │   └── live_stream.py      # LiveStreamManager singleton (capture / inference / display threads)
│   │   └── utils/
│   │       └── hash_utils.py       # SHA-256 helpers
│   ├── fabric.db                   # SQLite database (auto-created on startup)
│   ├── requirements.txt            # Backend Python deps
│   └── run.py                      # Uvicorn entrypoint (port 8000, reload)
├── frontend/
│   ├── public/
│   │   ├── logo.svg                # App logo
│   │   └── vite.svg
│   ├── services/
│   │   └── api.js                  # Axios client + endpoint groups (auth/images/live/dashboard)
│   ├── src/
│   │   ├── main.jsx                # ReactDOM root
│   │   ├── App.jsx                 # BrowserRouter + AuthProvider + route table
│   │   ├── index.css               # Tailwind + utility classes
│   │   ├── components/
│   │   │   ├── Navbar.jsx
│   │   │   ├── ProtectedRoute.jsx
│   │   │   └── LoadingSpinner.jsx
│   │   ├── context/
│   │   │   └── AuthContext.jsx     # login/register/logout + user state
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   ├── Register.jsx
│   │   │   ├── ImageUpload.jsx     # Drag-and-drop + detection table
│   │   │   └── LiveStream.jsx      # Source/model selectors + frame polling + recent defects
│   │   └── services/
│   │       └── api.js              # (alternate copy used by some pages)
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js              # Vite dev server on :3000 with /api proxy to :8000
│   ├── tailwind.config.js
│   └── postcss.config.js
├── uploads/                        # Saved uploaded + annotated images (served at /uploads/<filename>)
├── medium.pt                       # YOLOv8 medium model (≈52 MB)
├── nano.pt                         # YOLOv8 nano model (≈6 MB)
├── package.json                    # Root: uses `concurrently` (helper scripts may be added)
├── requirements.txt                # Top-level inference-only requirements (ultralytics + opencv + numpy + pillow)
├── test.png                        # Sample image
├── backend.log                     # Backend runtime log
├── frontend.log                    # Frontend runtime log
└── FYP-Fabric-Defcects-Detection-System/  # Inner git repo (with its own README.md)
```

---

## Defect Classes

Defined in `backend/app/config.py` (`CLASS_NAMES`, `CLASS_COLORS` — BGR for OpenCV):

| Class | Label  | Color (BGR)       | UI Badge Color |
|-------|--------|-------------------|----------------|
| 0     | hole   | (0, 0, 255) red   | red            |
| 1     | knot   | (0, 140, 255) orange | orange      |
| 2     | line   | (0, 255, 0) green | yellow         |
| 3     | stain  | (128, 0, 128) purple | green       |

Default confidence threshold: `CONF_THRESHOLD = 0.1`. Live stream inference uses `conf=0.4` at `imgsz=256`.

---

## Quick Start

1. **Install backend deps** (use the included `my_env` or a fresh venv):

   ```bash
   cd "backend"
   pip install -r requirements.txt
   ```

2. **Install frontend deps**:

   ```bash
   cd "../frontend"
   npm install
   ```

3. **Run the backend** (port 8000):

   ```bash
   python run.py
   ```

4. **Run the frontend** (port 3000, dev proxy `/api` → backend):

   ```bash
   npm run dev
   ```

5. Open <http://localhost:3000>, register a user, then use **Upload** or **Live Stream**.

---

## Backend (FastAPI)

### Configuration

`backend/app/config.py`:

- **Database**: SQLite file `backend/fabric.db` (auto-created via `init_db()` on startup).
- **JWT**: `SECRET_KEY` (env var), `ALGORITHM = "HS256"`, `ACCESS_TOKEN_EXPIRE_MINUTES = 60`.
- **Uploads**: directory `<project_root>/uploads/`, max upload `10 MB`.
- **Models**: `medium.pt` and `nano.pt` resolved relative to the project root (two levels above `backend/app/config.py`).
- **ESP32 URL**: `http://172.22.115.216:81/stream` (override with `ESP32_URL` env var).
- **CORS**: `allow_origins=["*"]`.

### Running the Backend

```bash
cd backend
python run.py
# uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

`/health` returns `{"status": "healthy"}` and `/` returns `{"message": "Fabric Defect Detection API", "status": "running"}`.

### Detector Service

`backend/app/services/detector.py` — singleton wrapper around a single YOLO model.

- `Detector()` — singleton, defaults to the **medium** model.
- `load_model("medium" | "nano")` — switch the active weights.
- `detect_from_array(img, conf_threshold=None)` — runs inference, draws bounding boxes + labels on a *copy* of the image, returns `(result_img, [{class, confidence, bbox}])`.
- The live stream manager does **not** use `Detector`; it loads its own YOLO instance so model switching does not affect image-upload responses.

### Live Stream Manager

`backend/app/services/live_stream.py` — singleton `LiveStreamManager`.

State machine:

```
start(source, model)
   ├─ load_model(model)
   ├─ source == "esp32" → connect to ESP32 MJPEG, parse JPEG markers (FFD8…FFD9)
   ├─ source == "local" → cv2.VideoCapture on first existing file among
   │                       fabric.mp4 / video23.mp4 / faults.mp4 in project root
   └─ spawn 3 daemon threads:
        • _capture_frames()  — read raw frames, push to bounded queue (maxsize=3)
        • _run_inference()   — pop frames, run YOLO @ imgsz=256 conf=0.4, draw boxes,
                                store each detection to PendingDefect with user_id,
                                keep last detection + running count
        • _display_loop()    — re-encode the latest detected frame as JPEG q=40,
                                update sliding-window FPS metric

stop() — joins threads, closes DB session
```

Public read methods (all lock-protected): `is_running()`, `get_source()`, `is_esp32_connected()`, `is_local_connected()`, `get_fps()`, `get_defect_count()`, `get_last_defect_name()`, `get_frame()` (returns latest JPEG bytes), `get_raw_frame()`.

Auto-fallback: after 3 failed ESP32 reads, switches to local video (one-shot).

> **Caveat**: `manager.set_user_id(1)` is hardcoded in `live.py:start_stream` — every live-stream detection is recorded against the user with id=1 regardless of which user started the stream.

### API Reference

All authenticated endpoints require `Authorization: Bearer <jwt>` (issued by `/api/auth/login`).

#### Authentication — `/api/auth`

| Method | Path           | Body                                  | Response                | Auth |
|--------|----------------|---------------------------------------|-------------------------|------|
| POST   | `/register`    | `UserCreate { username, email, password }` | `UserResponse`     | No   |
| POST   | `/login`       | `{ username, password }`              | `Token { access_token, token_type }` | No |
| GET    | `/me`          | —                                     | `UserResponse`          | Yes  |

#### Image Detection — `/api/images`

| Method | Path      | Body                              | Response                                       | Auth |
|--------|-----------|-----------------------------------|------------------------------------------------|------|
| POST   | `/upload` | multipart/form-data: `file` (image) | `{ filename, path }`                          | Yes  |
| POST   | `/detect` | multipart/form-data: `file` (image) | `DetectionResult { detections[], image_path }` | Yes  |

`/detect` saves the original and a `result_<uuid>.<ext>` annotated copy under `/uploads`, then records every detection to the `defects` table with `source="image_upload"` and the current `user_id`.

Static file: `GET /uploads/{filename}` returns the file or 404.

#### Live Stream — `/api/live`

| Method | Path                       | Params / Body                                     | Response | Auth |
|--------|----------------------------|---------------------------------------------------|----------|------|
| GET    | `/status`                  | —                                                 | `{ running, source, esp32_connected, local_connected, fps, defect_count, last_defect }` | No |
| POST   | `/start`                   | query: `source` (`esp32`\|`local`), `model` (`medium`\|`nano`) | `{ message, source, model }` | No |
| POST   | `/stop`                    | —                                                 | `{ message }` | No |
| GET    | `/frame`                   | —                                                 | `image/jpeg` (latest detected frame) | No |
| GET    | `/recent-defects?limit=N`  | —                                                 | List of `PendingDefect` (filtered by current user) | Yes |
| POST   | `/record-defect`           | query params: `defect_type, confidence, bbox_x1, bbox_y1, bbox_x2, bbox_y2, auto_save=false` | Either inserted directly into `defects` (if `auto_save=true`) or stored as `PendingDefect` | Yes |

#### Dashboard — `/api/dashboard`

| Method | Path                                     | Params                                              | Response | Auth |
|--------|------------------------------------------|-----------------------------------------------------|----------|------|
| GET    | `/stats`                                 | —                                                   | `DashboardStats { total_defects, defects_by_type, defects_by_source, recent_defects[10], pending_defects_count }` (per user; combines permanent + pending) | Yes |
| GET    | `/defects`                               | `skip`, `limit`, `defect_type`, `source`            | List of `DefectResponse` | Yes |
| GET    | `/chart/type-distribution`               | —                                                   | `ChartData { labels[], values[] }` | Yes |
| GET    | `/chart/daily-defects?days=7`            | `days`                                              | `ChartData` (per-day counts) | Yes |
| GET    | `/chart/confidence-distribution`         | —                                                   | `ChartData` (binned 0–100% in 10 buckets) | Yes |
| GET    | `/pending?skip=0&limit=50`               | `skip`, `limit`                                     | List of `PendingDefectResponse` | Yes |
| GET    | `/pending/stats`                         | —                                                   | `PendingStats { pending_count, pending_by_type }` | Yes |
| POST   | `/pending/add`                           | query params: `defect_type, confidence, bbox_*, image_path` | `{ message, id }` | Yes |
| POST   | `/pending/{id}/accept`                   | —                                                   | `{ message, defect_id }` — moves pending → defects (`source="pending_approval"`) | Yes |
| POST   | `/pending/{id}/delete`                   | —                                                   | `{ message }` | Yes |
| POST   | `/pending/convert-all`                   | —                                                   | `{ message, converted_count }` (source=`pending_conversion`) | Yes |
| POST   | `/pending/discard-all`                   | —                                                   | `{ message, discarded_count }` | Yes |

---

## Frontend (React + Vite)

### Frontend Configuration

`frontend/vite.config.js`:

- Dev server on port **3000**
- `/api` proxied to `http://localhost:8000` (so axios calls like `api.get('/api/...')` resolve to backend during dev)
- React plugin (`@vitejs/plugin-react`)

`frontend/tailwind.config.js` adds a `primary/secondary/accent` blue palette.

### Running the Frontend

```bash
cd frontend
npm install        # one time
npm run dev        # http://localhost:3000
npm run build      # production bundle to dist/
npm run preview    # serve the built bundle
```

### Routing

Defined in `frontend/src/App.jsx`:

| Path        | Component     | Access           |
|-------------|---------------|------------------|
| `/`         | Home / Hero   | Public           |
| `/login`    | `Login`       | Public (redirects to `/upload` if logged in) |
| `/register` | `Register`    | Public (redirects to `/login` if logged in)  |
| `/upload`   | `ImageUpload` | Protected (`<ProtectedRoute>`) |
| `/live`     | `LiveStream`  | Protected (`<ProtectedRoute>`) |
| `*`         | redirects to `/` | — |

`ProtectedRoute` reads `{ user, loading }` from `AuthContext`; if `loading`, it shows a centered spinner; if no `user`, it redirects to `/login`.

### Services Layer

Two `services/api.js` files exist (`frontend/services/api.js` and `frontend/src/services/api.js`). Both expose:

- `authAPI`: `login`, `register`, `getMe` → `/api/auth/*`
- `imageAPI` / `imagesAPI`: `upload`, `detect` → `/api/images/*`
- `liveAPI`: `start`, `stop`, `status`, `frame`, `recentDefects`, `recordDefect`
- `dashboardAPI`: stats, defects list, chart endpoints, pending list/accept/delete/convert/discard

A request interceptor injects `Authorization: Bearer <token>` from `localStorage.getItem('token')` if present.

---

## Data Models

SQLAlchemy ORM models in `backend/app/models/`:

### `users`
| Column        | Type            | Notes |
|---------------|-----------------|-------|
| id            | Integer PK      | auto-increment |
| username      | String(50) UQ   | indexed |
| email         | String(100) UQ  | indexed |
| password_hash | String(255)     | bcrypt |
| created_at    | DateTime        | `func.now()` server default |

### `defects` (confirmed)
| Column      | Type                         | Notes |
|-------------|------------------------------|-------|
| id          | Integer PK                   | auto-increment |
| user_id     | Integer FK → users.id        | ON DELETE SET NULL |
| defect_type | String(50)                   | indexed |
| confidence  | Float                        | 0.0–1.0 |
| bbox_x1..y2 | Integer (nullable)           | bounding box |
| image_path  | String(500) (nullable)       | upload path |
| source      | Enum(`image_upload`, `live_stream`, `pending_approval`, `pending_conversion`) | |
| detected_at | DateTime                     | indexed, `func.now()` |

### `pending_defects`
| Column      | Type            | Notes |
|-------------|-----------------|-------|
| id          | Integer PK      | auto-increment |
| user_id     | Integer FK → users.id | ON DELETE CASCADE, indexed |
| defect_type | String(50)      | indexed |
| confidence  | Float           | |
| bbox_x1..y2 | Integer (nullable) | |
| image_path  | String(500) (nullable) | |
| detected_at | DateTime        | indexed, `func.now()` |

> Note: the `Defect.source` column is declared as `Enum('image_upload', 'live_stream')`, but the dashboard router writes `source="pending_approval"` and `source="pending_conversion"` to it. SQLAlchemy will raise on insert if the enum constraint is strict on the chosen dialect.

---

## Authentication

- Passwords hashed with **bcrypt** via `passlib.context.CryptContext(schemes=["bcrypt"])`.
- Tokens signed with **HS256** using `SECRET_KEY` (default `"your-secret-key-change-in-production"` — override in production via env var).
- TTL: `ACCESS_TOKEN_EXPIRE_MINUTES = 60`.
- Claim `sub` = username.
- Frontend stores the token in `localStorage` under the key `token`; it is attached to every API request by the axios interceptor.

---

## Environment Variables

| Variable     | Default                                | Used By |
|--------------|----------------------------------------|---------|
| `SECRET_KEY` | `your-secret-key-change-in-production` | `app/config.py` (JWT signing) |
| `ESP32_URL`  | `http://172.22.115.216:81/stream`      | `app/config.py` (live stream capture) |

`backend/requirements.txt` (full list):

```
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
python-multipart>=0.0.6
pymysql>=1.1.0
sqlalchemy>=2.0.0
pydantic[email]>=2.0.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
```

Top-level `requirements.txt` (inference-only, lighter stack for direct YOLO use):

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
ultralytics==8.3.0
opencv-python==4.10.0.84
numpy==1.26.4
Pillow==10.4.0
requests==2.32.3
```

> `pymysql` is in `backend/requirements.txt` but is unused — the project is on SQLite. `fastapi/uvicorn/ultralytics/opencv-python/numpy/Pillow/requests` are not in `backend/requirements.txt` and must come from the top-level `requirements.txt` (or be installed manually) for the routers/services to actually run.

---

## Model Files

| File       | Size  | Purpose |
|------------|-------|---------|
| `medium.pt`| ~52 MB| More accurate YOLOv8 weights (default for image upload + live) |
| `nano.pt`  | ~6 MB | Faster YOLOv8 weights (toggle on the live-stream page) |

`MEDIUM_MODEL` and `NANO_MODEL` in `config.py` resolve to these paths:

```python
PROJECT_ROOT = os.path.dirname(BASE_DIR)        # FYP Final/
MEDIUM_MODEL  = os.path.join(PROJECT_ROOT, "medium.pt")
NANO_MODEL    = os.path.join(PROJECT_ROOT, "nano.pt")
```

---

## Notes & Caveats

- **Single-user live stream attribution**: `live.py:start_stream` calls `manager.set_user_id(1)`, so all live-stream detections are persisted against the user with `id=1` regardless of who pressed *Start*.
- **Enum strictness**: `Defect.source` is a SQLAlchemy `Enum('image_upload', 'live_stream')` but dashboard routes insert `pending_approval` and `pending_conversion`. Depending on dialect/version, these inserts may fail.
- **Untracked uploads directory**: `uploads/` exists at the project root but is empty — only files written at runtime live there (saved originals and `result_<uuid>.<ext>` annotated images).
- **Frontend duplicate services**: `frontend/services/api.js` and `frontend/src/services/api.js` both exist. The pages currently import from `../services/api` (i.e., `src/services/api.js`); the top-level copy in `frontend/services/api.js` is a parallel module with a slightly different base-URL strategy (no `/api` prefix in baseURL, paths include the prefix).
- **Local fallback video names**: `LiveStreamManager._find_local_video()` looks for `fabric.mp4`, `video23.mp4`, or `faults.mp4` in the project root.
- **Inner git repo**: `FYP-Fabric-Defcects-Detection-System/` is its own git repository (`.git/` present), separate from the outer project. Its README describes the same project from a different starting point.
- **Logs**: `backend.log` and `frontend.log` at the project root capture the most recent run output for quick debugging.
- **CORS**: open (`allow_origins=["*"]`) — fine for local development, must be tightened for production.
- **`btn-success` / `btn-xs`** are referenced in `LiveStream.jsx` but not defined in `index.css`. They will render as plain text. Add `btn-success` (`bg-green-600 ...`) and `.btn-xs` (`px-2 py-1 text-xs`) to fix.

---

**Author / Course**: Final Year Project — Fabric Defects Detection System. Models trained for the four classes: *hole*, *knot*, *line*, *stain*.
