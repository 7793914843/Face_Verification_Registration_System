from fastapi import APIRouter, Request, HTTPException, status
from backend.schemas.schemas import SuccessResponse, FaceIdentificationResponseData, FaceCrop, FailureResponse, FaceIdentificationRequest
from backend.source.utils import base64_to_cv2, cv2_to_base64
from backend.logger import logger
import face_processing

router = APIRouter(prefix="/api", tags=["Face Detection"])

@router.post("/identify_faces", response_model=SuccessResponse[FaceIdentificationResponseData])
async def identify_faces(request: Request, payload: FaceIdentificationRequest):
    # Ensure user is authenticated
    if "user_id" not in request.session:
        logger.warning("Unauthorized access attempt to /identify_faces")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized. Please log in first."
        )
        
    image_b64 = payload.image
    if not image_b64:
        logger.error("Missing image in /identify_faces request")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing image data."
        )
        
    img = base64_to_cv2(image_b64)
    if img is None:
        logger.error("Failed to decode base64 image in /identify_faces")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image data."
        )
        
    try:
        logger.info("Running face detection using YOLO model")
        faces = face_processing.detect_faces(img)
    except Exception as e:
        logger.exception("Error running face detection model")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Detection error: {str(e)}"
        )
        
    cropped_faces_b64 = []
    h, w = img.shape[:2]
    
    for i, face in enumerate(faces):
        box = face['box']
        x1, y1, x2, y2 = map(int, box)
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        
        cropped = img[y1:y2, x1:x2]
        if cropped.size > 0:
            b64 = cv2_to_base64(cropped)
            if b64:
                cropped_faces_b64.append(
                    FaceCrop(id=i + 1, image=b64)
                )
                
    logger.info(f"Successfully detected {len(faces)} faces")
    
    return SuccessResponse(
        success=True,
        data=FaceIdentificationResponseData(
            count=len(faces),
            faces=cropped_faces_b64
        )
    )
