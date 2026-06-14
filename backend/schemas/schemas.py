from pydantic import BaseModel
from typing import Any, Optional, Dict, List, Generic, TypeVar

T = TypeVar('T')

class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T

class FailureResponse(BaseModel):
    success: bool = False
    message: str

class RegistrationRequest(BaseModel):
    username: str
    password: str
    confirm_password: str
    image: str  # Base64 string

class RegistrationResponseData(BaseModel):
    message: str

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponseData(BaseModel):
    username: str
    message: str

class CheckSessionResponseData(BaseModel):
    logged_in: bool
    username: Optional[str] = None

class FaceVerificationRequest(BaseModel):
    image: str

class FaceVerificationResponseData(BaseModel):
    matched_user: Optional[str]
    similarity_threshold: float
    bounding_box_coordinates: List[List[int]]
    verification_status: str
    image: Optional[str] = None  # Base64 string with drawn bounding box(es)

class FaceIdentificationRequest(BaseModel):
    image: str

class FaceCrop(BaseModel):
    id: int
    image: str

class FaceIdentificationResponseData(BaseModel):
    count: int
    faces: List[FaceCrop]

class BodyIdentificationRequest(BaseModel):
    image: str

class BodyIdentificationResponseData(BaseModel):
    count: int
    image: str  # Base64 annotated image

class ImageResizeRequest(BaseModel):
    image: str
    width: int
    height: int

class ImageResizeResponseData(BaseModel):
    original_width: int
    original_height: int
    resized_width: int
    resized_height: int
    image: str
