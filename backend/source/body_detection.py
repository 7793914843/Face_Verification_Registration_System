import cv2
from fastapi import APIRouter, Request, HTTPException, status
from backend.schemas.schemas import SuccessResponse, BodyIdentificationResponseData, BodyIdentificationRequest
from backend.source.utils import base64_to_cv2, cv2_to_base64
from backend.logger import logger
import face_processing

router = APIRouter(prefix="/api", tags=["Body Detection"])

@router.post("/identify_bodies", response_model=SuccessResponse[BodyIdentificationResponseData])
async def identify_bodies(request: Request, payload: BodyIdentificationRequest):
    # Ensure user is authenticated
    if "user_id" not in request.session:
        logger.warning("Unauthorized access attempt to /identify_bodies")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized. Please log in first."
        )
        
    image_b64 = payload.image
    if not image_b64:
        logger.error("Missing image in /identify_bodies request")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing image data."
        )
        
    img = base64_to_cv2(image_b64)
    if img is None:
        logger.error("Failed to decode base64 image in /identify_bodies")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image data."
        )
        
    try:
        logger.info("Running body detection using YOLO model")
        bodies = face_processing.detect_bodies(img)
    except Exception as e:
        logger.exception("Error running body detection model")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Detection error: {str(e)}"
        )
        
    # Draw bounding boxes on the image copy
    annotated_img = img.copy()
    for i, body in enumerate(bodies):
        x1, y1, x2, y2, conf = body
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        
        # Premium violet/cyan bounding box
        cv2.rectangle(annotated_img, (x1, y1), (x2, y2), (255, 0, 128), 2)
        
        # Bounding box label
        label = f"Person {i+1} ({round(conf * 100, 1)}%)"
        cv2.putText(annotated_img, label, (x1, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)
                    
    b64_annotated = cv2_to_base64(annotated_img)
    
    logger.info(f"Successfully detected {len(bodies)} persons")
    
    return SuccessResponse(
        success=True,
        data=BodyIdentificationResponseData(
            count=len(bodies),
            image=b64_annotated
        )
    )
