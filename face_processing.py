import os
import cv2
import numpy as np
from ultralytics import YOLO
import insightface

# Global model variables
face_model = None
body_model = None
rec_model = None

def load_models():
    global face_model, body_model, rec_model
    
    # Load YOLO face detector
    face_model_path = os.path.join(os.path.dirname(__file__), "models", "yolov8n-face.pt")
    if not os.path.exists(face_model_path):
        raise FileNotFoundError(f"YOLO face model not found at {face_model_path}")
    face_model = YOLO(face_model_path)
    
    # Load YOLO body detector (will automatically load or download yolov8n.pt)
    body_model = YOLO("yolov8n.pt")
    
    # Load ArcFace recognition model
    rec_model_path = os.path.expanduser("~/.insightface/models/buffalo_l/w600k_r50.onnx")
    if not os.path.exists(rec_model_path):
        # Trigger insightface download by initializing FaceAnalysis briefly if needed
        print("ArcFace ONNX model not found, pre-initializing FaceAnalysis to trigger download...")
        app = insightface.app.FaceAnalysis(providers=['CPUExecutionProvider'])
        app.prepare(ctx_id=0)
    
    if os.path.exists(rec_model_path):
        rec_model = insightface.model_zoo.get_model(rec_model_path, providers=['CPUExecutionProvider'])
        rec_model.prepare(ctx_id=0)
    else:
        raise FileNotFoundError("Could not find or download ArcFace model w600k_r50.onnx")

def detect_faces(image):
    """
    Detect faces using YOLO face model.
    Returns a list of dicts: [{'box': [x1, y1, x2, y2], 'keypoints': [[x,y],...] or None}]
    """
    if face_model is None:
        load_models()
        
    results = face_model(image, verbose=False)
    detections = []
    
    if len(results) == 0:
        return detections
        
    boxes = results[0].boxes
    keypoints = results[0].keypoints
    
    for i in range(len(boxes)):
        box = boxes[i].xyxy[0].cpu().numpy().tolist() # [x1, y1, x2, y2]
        conf = float(boxes[i].conf[0].cpu().numpy())
        
        # We only want confident detections (e.g. > 0.4)
        if conf < 0.4:
            continue
            
        kpts = None
        if keypoints is not None and len(keypoints.xy) > i:
            # keypoints.xy[i] contains keypoints for i-th face
            kpts = keypoints.xy[i].cpu().numpy().tolist()
            
        detections.append({
            'box': box,
            'confidence': conf,
            'keypoints': kpts
        })
        
    return detections

def align_crop_face(image, detection):
    """
    Align and crop face according to ArcFace requirements (112x112).
    If keypoints are present, uses similarity transform.
    Otherwise, falls back to direct bounding box crop and resize.
    """
    box = detection['box']
    kpts = detection['keypoints']
    
    # 1. Try keypoint-based alignment
    if kpts is not None and len(kpts) == 5:
        # Check that landmarks are not all zeros (which YOLO keypoints.xy can be if not detected)
        src_pts = np.array(kpts, dtype=np.float32)
        if not np.allclose(src_pts, 0.0):
            # ArcFace reference landmarks for 112x112
            dst_pts = np.array([
                [38.2946, 51.6963],  # Left eye
                [73.5318, 51.5014],  # Right eye
                [56.0252, 71.7366],  # Nose
                [41.5493, 92.3655],  # Left mouth corner
                [70.7299, 92.2041]   # Right mouth corner
            ], dtype=np.float32)
            
            # Estimate similarity transform
            M, inliers = cv2.estimateAffinePartial2D(src_pts, dst_pts)
            if M is not None:
                warped = cv2.warpAffine(image, M, (112, 112))
                return warped
                
    # 2. Fallback to standard crop & resize
    h, w = image.shape[:2]
    x1, y1, x2, y2 = map(int, box)
    # Clamp coordinates to image boundaries
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    
    cropped = image[y1:y2, x1:x2]
    if cropped.size > 0:
        return cv2.resize(cropped, (112, 112))
    return None

def get_arcface_embedding(aligned_face):
    """
    Generate face embedding using ArcFace.
    Returns a normalized list of 512 floats.
    """
    if rec_model is None:
        load_models()
        
    # Model expects 112x112 BGR image. Let's make sure it is exactly that.
    if aligned_face.shape[:2] != (112, 112):
        aligned_face = cv2.resize(aligned_face, (112, 112))
        
    feat = rec_model.get_feat(aligned_face)
    if feat is None:
        return None
        
    # Get 1D array of 512 features
    embedding = feat[0]
    
    # L2 normalize
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm
        
    return embedding.tolist()

def cosine_similarity(emb1, emb2):
    """
    Calculate similarity between two face embeddings.
    Since embeddings are L2 normalized, similarity is the dot product.
    """
    if emb1 is None or emb2 is None:
        return 0.0
    return float(np.dot(emb1, emb2))

def detect_bodies(image):
    """
    Detect persons using YOLOv8 body model.
    Returns list of bounding boxes: [[x1, y1, x2, y2, confidence], ...]
    """
    if body_model is None:
        load_models()
        
    results = body_model(image, verbose=False)
    persons = []
    
    if len(results) == 0:
        return persons
        
    boxes = results[0].boxes
    for box in boxes:
        cls_id = int(box.cls[0].cpu().numpy())
        conf = float(box.conf[0].cpu().numpy())
        
        # Class 0 is person, and we check confidence > 0.4
        if cls_id == 0 and conf > 0.4:
            xyxy = box.xyxy[0].cpu().numpy().tolist()
            persons.append(xyxy + [conf])
            
    return persons
