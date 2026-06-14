import bcrypt
from fastapi import APIRouter, Request, HTTPException, status
from backend.schemas.schemas import (
    SuccessResponse, RegistrationRequest, RegistrationResponseData,
    LoginRequest, LoginResponseData, CheckSessionResponseData
)
from backend.source.utils import base64_to_cv2
from backend.logger import logger
from database import SessionLocal, User
import face_processing

router = APIRouter(prefix="/api", tags=["Authentication"])

@router.post("/register", response_model=SuccessResponse[RegistrationResponseData], status_code=status.HTTP_201_CREATED)
async def register(request: Request, payload: RegistrationRequest):
    username = payload.username.strip()
    password = payload.password
    confirm_password = payload.confirm_password
    image_b64 = payload.image
    
    # Validation checks
    if not username or not password or not image_b64:
        logger.error("Registration failed: missing fields")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All fields and face capture are required."
        )
        
    if password != confirm_password:
        logger.error("Registration failed: password mismatch")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match."
        )
        
    img = base64_to_cv2(image_b64)
    if img is None:
        logger.error("Registration failed: invalid image encoding")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image data."
        )
        
    # Face detection check
    try:
        logger.info("Running face detection for registration")
        faces = face_processing.detect_faces(img)
    except Exception as e:
        logger.exception("Face detection model failure during registration")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running face detection: {str(e)}"
        )
        
    face_count = len(faces)
    if face_count == 0:
        logger.info("Registration failed: no face detected")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No face detected. Please try again."
        )
    elif face_count > 1:
        logger.info(f"Registration failed: multiple faces detected ({face_count})")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Multiple faces detected ({face_count}). Registration requires exactly one face."
        )
        
    # Process face biometrics
    try:
        logger.info("Aligning and extracting face embedding for registration")
        aligned_face = face_processing.align_crop_face(img, faces[0])
        if aligned_face is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Face alignment failed. Please position your face clearly in the camera."
            )
            
        embedding = face_processing.get_arcface_embedding(aligned_face)
        if embedding is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to generate face embedding."
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Biometric extraction failed during registration")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing face biometrics: {str(e)}"
        )
        
    # Hash password using bcrypt
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
    
    # Save to PostgreSQL
    db = SessionLocal()
    try:
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            logger.warning(f"Registration failed: username '{username}' already taken")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username is already taken."
            )
            
        new_user = User(
            username=username,
            password_hash=password_hash,
            face_embedding=embedding
        )
        db.add(new_user)
        db.commit()
        logger.info(f"Successfully registered user '{username}'")
        
        return SuccessResponse(
            success=True,
            data=RegistrationResponseData(message="Registration successful! You can now log in.")
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.exception("Database insert failure during registration")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database save error: {str(e)}"
        )
    finally:
        db.close()

@router.post("/login", response_model=SuccessResponse[LoginResponseData])
async def login(request: Request, payload: LoginRequest):
    username = payload.username.strip()
    password = payload.password
    
    if not username or not password:
        logger.error("Login failed: missing credentials")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password are required."
        )
        
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            logger.warning(f"Login failed: invalid username '{username}'")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password."
            )
            
        # Verify bcrypt hash
        if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            # Store session keys
            request.session["user_id"] = user.id
            request.session["username"] = user.username
            logger.info(f"Successfully logged in user '{username}'")
            
            return SuccessResponse(
                success=True,
                data=LoginResponseData(
                    username=user.username,
                    message=f"Welcome back, {user.username}!"
                )
            )
        else:
            logger.warning(f"Login failed: incorrect password for '{username}'")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password."
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Database error during login")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(e)}"
        )
    finally:
        db.close()

@router.post("/logout", response_model=SuccessResponse[RegistrationResponseData])
async def logout(request: Request):
    username = request.session.get("username", "Unknown")
    request.session.clear()
    logger.info(f"Logged out session for user '{username}'")
    return SuccessResponse(
        success=True,
        data=RegistrationResponseData(message="Logged out successfully.")
    )

@router.get("/check_session", response_model=SuccessResponse[CheckSessionResponseData])
async def check_session(request: Request):
    if "user_id" in request.session:
        logger.info(f"Session check: active session found for '{request.session['username']}'")
        return SuccessResponse(
            success=True,
            data=CheckSessionResponseData(
                logged_in=True,
                username=request.session["username"]
            )
        )
    logger.info("Session check: no active session found")
    return SuccessResponse(
        success=True,
        data=CheckSessionResponseData(logged_in=False)
    )
