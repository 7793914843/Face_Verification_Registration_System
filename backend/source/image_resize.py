import cv2
from fastapi import APIRouter, Request, HTTPException, status
from backend.schemas.schemas import SuccessResponse, ImageResizeResponseData, ImageResizeRequest
from backend.source.utils import base64_to_cv2, cv2_to_base64
from backend.logger import logger

router = APIRouter(prefix="/api", tags=["Image Resizing"])

@router.post("/resize_image", response_model=SuccessResponse[ImageResizeResponseData])
async def resize_image(request: Request, payload: ImageResizeRequest):
    # Ensure user is authenticated
    if "user_id" not in request.session:
        logger.warning("Unauthorized access attempt to /resize_image")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized. Please log in first."
        )
        
    image_b64 = payload.image
    target_width = payload.width
    target_height = payload.height
    
    if not image_b64:
        logger.error("Missing image in /resize_image request")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing image data."
        )
        
    img = base64_to_cv2(image_b64)
    if img is None:
        logger.error("Failed to decode base64 image in /resize_image")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image data."
        )
        
    # Validate dimensions
    if target_width <= 0 or target_height <= 0:
        logger.error("Dimensions must be positive integers")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Width and height must be positive integers."
        )
        
    if target_width > 4000 or target_height > 4000:
        logger.error("Dimensions exceeded maximum allowed size (4000x4000)")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dimensions are too large (max 4000x4000)."
        )
        
    # Resize using OpenCV (CUBIC interpolation for quality)
    logger.info(f"Resizing image to {target_width}x{target_height}")
    resized_img = cv2.resize(img, (target_width, target_height), interpolation=cv2.INTER_CUBIC)
    b64_resized = cv2_to_base64(resized_img)
    
    orig_h, orig_w = img.shape[:2]
    
    logger.info(f"Image resized successfully from {orig_w}x{orig_h} to {target_width}x{target_height}")
    
    return SuccessResponse(
        success=True,
        data=ImageResizeResponseData(
            original_width=orig_w,
            original_height=orig_h,
            resized_width=target_width,
            resized_height=target_height,
            image=b64_resized
        )
    )
