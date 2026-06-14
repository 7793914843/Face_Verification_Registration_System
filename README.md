# Aegis Biometrics - Face Registration & Verification System

A secure, premium biometric identity and verification platform built using FastAPI, PostgreSQL, YOLOv8, and ArcFace. This platform supports secure user sign-up (via facial credential registration), login, face verification, face identification (multi-face crops), body identification, and image resizing.

---

## Folder Structure

```text
FaceRegistrationAndVerification-main/
├── app.py                     # Main FastAPI application entrypoint
├── database.py                # Database models and session helpers (PostgreSQL/SQLAlchemy)
├── face_processing.py         # AI Model runner utilities (YOLO Face, YOLO Body, ArcFace)
├── requirements.txt           # Python application dependencies
├── yolov8n.pt                 # Pre-trained YOLOv8 object detection model weight
├── models/
│   └── yolov8n-face.pt        # YOLOv8 face detection model weight
├── static/                    # Frontend SPA files
│   ├── index.html             # UI layout (styled with Tailwind CSS)
│   ├── app.js                 # Frontend interactivity and API communication logic
│   └── style.css              # Custom styling definitions
├── logs/                      # Log files storage folder
│   └── app.log                # JSON-formatted application logs (generated at runtime)
└── backend/                   # Refactored backend package
    ├── __init__.py
    ├── logger.py              # Structured JSON logger configuration
    ├── schemas/               # Request & Response Pydantic models (DTOs)
    │   ├── __init__.py
    │   └── schemas.py
    └── source/                # Core business logic and API routers
        ├── __init__.py
        ├── utils.py           # General utility helper functions
        ├── auth.py            # Signup, Login, Logout, and Session routers
        ├── face_detection.py  # Face identification and cropping router
        ├── body_detection.py  # Body detection and annotation router
        ├── image_resize.py    # Image resizing and validation router
        └── face_verification.py # Face verification and database-wide face matching router
```

---

## Features

1. **Authentication Flow**:
   - Secure username & password sign-up along with a required face credential capture.
   - Session-based user login, session status checks, and logout.
   - Successful signup automatically alerts the user and redirects them to the Log In panel.

2. **Webcam & Image Upload Support**:
   - Every input interface allows users to choose between capturing a frame from their Webcam or uploading a local image file.
   - Both inputs go through the exact same processing and validation pipeline on the backend.

3. **Face Verification**:
   - Extracts the ArcFace biometric embedding of a detected face.
   - Compares it against all registered users' embeddings in the PostgreSQL database using Cosine Similarity.
   - Returns the matched username, verification status (`verified` or `failed`), similarity score threshold, and draws bounding boxes around all detected faces (highlighting the primary matched face in green if successful, or red if failed).

4. **Face Identification & Multi-Crop**:
   - Detects all faces present in the photo using the YOLO face model.
   - Crops each detected face individually and allows downloading each crop with a custom name.

5. **Body Detection**:
   - Traces all persons present in the scene using YOLOv8, overlaying premium violet/cyan bounding boxes and labels.

6. **Image Resizing**:
   - Resizes any photo to custom dimensions using OpenCV `INTER_CUBIC` interpolation.
   - Prevents scaling out of the safety boundary (50% to 200% scaling check alert).

---

## Backend Architecture

The backend has been refactored using a modular, decoupled architecture adhering to **Clean Architecture** principles:

- **FastAPI Core (`app.py`)**: Responsible only for initializing the server, registering routers, configuring CORS, session middleware, exception handling, and handling lifespan startup/shutdown hooks.
- **API Routers (`backend/source/`)**: Contain isolated, modular routers for different domains (`auth`, `face_detection`, `body_detection`, `image_resize`, `face_verification`). Each route relies on Pydantic schemas for request/response serialization.
- **DTO Layer (`backend/schemas/`)**: Houses Pydantic schemas which define request and response models. Output payloads follow a strict success/failure wrapping convention.
- **Data Access (`database.py`)**: Uses SQLAlchemy ORM to manage connection pooling and transactions with PostgreSQL.
- **Structured Logging (`backend/logger.py`)**: Integrates Python's standard logging module with `python-json-logger` to record JSON-formatted logs under `logs/app.log`.

---

## API Documentation

All successful API responses wrap their data inside a unified DTO wrapper:

### Success Format
```json
{
  "success": true,
  "data": { ... }
}
```

### Failure Format
```json
{
  "success": false,
  "message": "Error details here"
}
```

### Endpoints

#### 1. Authentication
* **POST `/api/register`**
  - **Request**: `RegistrationRequest` (fields: `username`, `password`, `confirm_password`, `image` (base64))
  - **Response Status 201**: `SuccessResponse[RegistrationResponseData]`
* **POST `/api/login`**
  - **Request**: `LoginRequest` (fields: `username`, `password`)
  - **Response Status 200**: `SuccessResponse[LoginResponseData]`
* **POST `/api/logout`**
  - **Response Status 200**: `SuccessResponse[RegistrationResponseData]`
* **GET `/api/check_session`**
  - **Response Status 200**: `SuccessResponse[CheckSessionResponseData]`

#### 2. Face Verification
* **POST `/api/verify_face`**
  - **Request**: `FaceVerificationRequest` (fields: `image` (base64))
  - **Response Status 200**: `SuccessResponse[FaceVerificationResponseData]`
  - *Note: Returns `matched_user`, `similarity_threshold`, `bounding_box_coordinates`, `verification_status`, and the annotated `image` (base64).*

#### 3. Face Identification
* **POST `/api/identify_faces`**
  - **Request**: `FaceIdentificationRequest` (fields: `image` (base64))
  - **Response Status 200**: `SuccessResponse[FaceIdentificationResponseData]`

#### 4. Body Detection
* **POST `/api/identify_bodies`**
  - **Request**: `BodyIdentificationRequest` (fields: `image` (base64))
  - **Response Status 200**: `SuccessResponse[BodyIdentificationResponseData]`

#### 5. Image Resizing
* **POST `/api/resize_image`**
  - **Request**: `ImageResizeRequest` (fields: `image` (base64), `width` (int), `height` (int))
  - **Response Status 200**: `SuccessResponse[ImageResizeResponseData]`

---

## Environment Variables

Create a `.env` file in the root directory:

```env
SECRET_KEY=your_session_secret_key_here
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=your_postgres_user
DB_PASSWORD=your_postgres_password
```

---

## Installation & Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Database Setup**:
   Ensure PostgreSQL is running and a database matching `DB_NAME` is created.

3. **Running the Application**:
   Run the FastAPI server using `uvicorn`:
   ```bash
   python app.py
   ```
   The backend and embedded frontend will be available at `http://127.0.0.1:5001`.

---

## Troubleshooting Guide

- **Database Connection Failures**: Check that PostgreSQL service is running and credentials in `.env` match.
- **Model Download Issues**: On initial startup, the ArcFace model (`w600k_r50.onnx`) is downloaded automatically if missing. Ensure your machine has an active internet connection.
- **Webcam Errors**: Ensure your browser has camera access permissions allowed for `http://127.0.0.1:5001`.
- **Validation Errors**: Ensure image input strings are sent as valid base64-encoded Data URLs (e.g. `data:image/jpeg;base64,...`).

---

## Future Improvements

1. **Enhanced Model Execution**: Implement GPU execution providers (`CUDAExecutionProvider` for ONNX Runtime) to improve model latency.
2. **Liveness Detection**: Introduce blink or depth checking to prevent spoofing via printed/digital photos.
3. **JWT Authentication**: Migrate from session-based cookies to secure JSON Web Tokens (JWT) for stateless API authentication.
