import cv2
import numpy as np
import base64
from backend.logger import logger

def base64_to_cv2(b64_string):
    try:
        if not b64_string:
            return None
        if "," in b64_string:
            b64_string = b64_string.split(",")[1]
        img_data = base64.b64decode(b64_string)
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        logger.error(f"Error decoding base64 image: {str(e)}")
        return None

def cv2_to_base64(img):
    try:
        if img is None:
            return None
        _, buffer = cv2.imencode('.jpg', img)
        b64_string = base64.b64encode(buffer).decode('utf-8')
        return "data:image/jpeg;base64," + b64_string
    except Exception as e:
        logger.error(f"Error encoding image to base64: {str(e)}")
        return None
