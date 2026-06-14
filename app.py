import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

# Import database, face processing, and logger
from database import init_db
import face_processing
from backend.logger import logger

# Import routers
from backend.source.auth import router as auth_router
from backend.source.face_detection import router as face_detection_router
from backend.source.body_detection import router as body_detection_router
from backend.source.image_resize import router as image_resize_router
from backend.source.face_verification import router as face_verification_router

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Application startup
    logger.info("Application is starting up...")
    init_db()
    try:
        logger.info("Pre-loading YOLO and ArcFace models...")
        face_processing.load_models()
        logger.info("Models pre-loaded successfully!")
    except Exception as e:
        logger.warning(f"Model pre-loading failed. They will load on first request: {str(e)}")
    
    yield
    
    # Application shutdown
    logger.info("Application is shutting down...")

app = FastAPI(
    title="Aegis Biometrics Identity Platform",
    description="Refactored Biometric Authentication System with FastAPI",
    version="1.0.0",
    lifespan=lifespan
)

# Add session middleware
SECRET_KEY = os.getenv("SECRET_KEY", "face_verification_secret_session_key_2026")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Exception handling
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc: StarletteHTTPException):
    logger.error(f"HTTP error {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.detail}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    errors_summary = "; ".join([f"{err['loc'][-1]}: {err['msg']}" for err in exc.errors()])
    logger.error(f"Validation error: {errors_summary}")
    return JSONResponse(
        status_code=400,
        content={"success": False, "message": f"Validation error: {errors_summary}"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    logger.exception("Unhandled application exception")
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": f"Internal server error: {str(exc)}"}
    )

# Register routers
app.include_router(auth_router)
app.include_router(face_detection_router)
app.include_router(body_detection_router)
app.include_router(image_resize_router)
app.include_router(face_verification_router)

# Serve static files from static directory
# We mount it at the root (/) to serve index.html, style.css, app.js directly.
# Since routers are registered first, they take priority.
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=5001, reload=True)
