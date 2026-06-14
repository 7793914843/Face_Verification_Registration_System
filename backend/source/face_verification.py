import cv2
from fastapi import APIRouter, Request, HTTPException, status
from backend.schemas.schemas import SuccessResponse, FaceVerificationResponseData, FaceVerificationRequest
from backend.source.utils import base64_to_cv2, cv2_to_base64
from backend.logger import logger
from database import SessionLocal, User
import face_processing

router = APIRouter(prefix="/api", tags=["Face Verification"])

@router.post("/verify_face", response_model=SuccessResponse[FaceVerificationResponseData])
async def verify_face(request: Request, payload: FaceVerificationRequest):
    # Ensure user is authenticated
    if "user_id" not in request.session:
        logger.warning("Unauthorized access attempt to /verify_face")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized. Please log in first."
        )
        
    image_b64 = payload.image
    if not image_b64:
        logger.error("Missing image in /verify_face request")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing image data."
        )
        
    img = base64_to_cv2(image_b64)
    if img is None:
        logger.error("Failed to decode base64 image in /verify_face")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image data."
        )
        
    try:
        logger.info("Running face detection in /verify_face")
        faces = face_processing.detect_faces(img)
    except Exception as e:
        logger.exception("Error running face detection model")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Face detection error: {str(e)}"
        )
        
    face_count = len(faces)
    if face_count == 0:
        logger.info("No face detected during verification")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No face detected. Please try again."
        )
        
    # Extract coordinates for all detected faces
    bounding_box_coordinates = []
    h, w = img.shape[:2]
    for face in faces:
        x1, y1, x2, y2 = map(int, face['box'])
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        bounding_box_coordinates.append([x1, y1, x2, y2])
        
    # We will verify the largest/primary face (index 0) against the database
    primary_face = faces[0]
    
    try:
        logger.info("Extracting face embedding for the primary face")
        aligned_face = face_processing.align_crop_face(img, primary_face)
        if aligned_face is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Face alignment failed."
            )
            
        capture_embedding = face_processing.get_arcface_embedding(aligned_face)
        if capture_embedding is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Embedding extraction failed."
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error during face biometrics processing")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Biometric processing error: {str(e)}"
        )
        
    # Retrieve all users from DB
    db = SessionLocal()
    best_similarity = -1.0
    matched_user = None
    threshold = 0.45
    
    try:
        logger.info("Fetching registered users from database to compare")
        users = db.query(User).all()
        
        for user in users:
            if user.face_embedding is None:
                continue
            sim = face_processing.cosine_similarity(user.face_embedding, capture_embedding)
            if sim > best_similarity:
                best_similarity = sim
                if sim >= threshold:
                    matched_user = user.username
    except Exception as e:
        logger.exception("Database error during face verification matching")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    finally:
        db.close()
        
    # Set status and labels
    verified = best_similarity >= threshold
    status_str = "verified" if verified else "failed"
    display_user = matched_user if verified else "No Valid Match Found"
    
    logger.info(f"Verification result: status={status_str}, user={display_user}, similarity={best_similarity:.4f}")
    
    # Draw boxes on duplicate image
    annotated_img = img.copy()
    for idx, box_coords in enumerate(bounding_box_coordinates):
        x1, y1, x2, y2 = box_coords
        
        if idx == 0:
            # Primary face (being matched)
            color = (0, 255, 0) if verified else (0, 0, 255) # Green if verified, Red if failed
            label = f"{display_user} ({round(best_similarity * 100, 1)}%)"
        else:
            # Secondary faces
            color = (255, 0, 128) # Violet/cyan
            label = "Face Detected"
            
        cv2.rectangle(annotated_img, (x1, y1), (x2, y2), color, 2)
        cv2.putText(annotated_img, label, (x1, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)
                    
    b64_annotated = cv2_to_base64(annotated_img)
    
    return SuccessResponse(
        success=True,
        data=FaceVerificationResponseData(
            matched_user=display_user,
            similarity_threshold=threshold,
            bounding_box_coordinates=bounding_box_coordinates,
            verification_status=status_str,
            image=b64_annotated
        )
    )
