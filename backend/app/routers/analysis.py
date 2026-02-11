"""
Analysis Router

Handles iris image upload and analysis endpoints.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import json

from ..services.image_processor import IrisImageProcessor
from ..services.llm_agents import IridologyAgentManager

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

# Initialize services
image_processor = IrisImageProcessor()
agent_manager = IridologyAgentManager()


@router.post("/analyze")
async def analyze_iris(
    patient_name: str = Form(...),
    notes: Optional[str] = Form(None),
    left_iris: Optional[UploadFile] = File(None),
    right_iris: Optional[UploadFile] = File(None)
):
    """
    Analyze iris images using all three doctor methodologies.

    - Upload one or both iris images (left and/or right)
    - Provide patient name and optional notes
    - Returns analysis from Peczely, Jensen, and Morse perspectives
    """
    if not left_iris and not right_iris:
        raise HTTPException(status_code=400, detail="At least one iris image is required")

    left_features = None
    right_features = None
    left_data = None
    right_data = None

    # Process left iris if provided
    if left_iris:
        left_data_raw = await left_iris.read()
        # Preprocess: remove glare and enhance for better analysis
        left_data = image_processor.preprocess_image_bytes(left_data_raw)
        left_features = await image_processor.process_image(left_data_raw, "left")

    # Process right iris if provided
    if right_iris:
        right_data_raw = await right_iris.read()
        # Preprocess: remove glare and enhance for better analysis
        right_data = image_processor.preprocess_image_bytes(right_data_raw)
        right_features = await image_processor.process_image(right_data_raw, "right")

    # Run analysis with all three agents (using preprocessed images for vision analysis)
    analysis_results = await agent_manager.analyze_all(
        left_iris_features=left_features,
        right_iris_features=right_features,
        patient_name=patient_name,
        notes=notes,
        left_iris_image=left_data,
        right_iris_image=right_data
    )

    return {
        "patient_name": patient_name,
        "notes": notes,
        "image_analysis": {
            "left_iris": left_features,
            "right_iris": right_features
        },
        "doctor_analyses": analysis_results
    }


@router.post("/analyze/{doctor}")
async def analyze_iris_single_doctor(
    doctor: str,
    patient_name: str = Form(...),
    notes: Optional[str] = Form(None),
    left_iris: Optional[UploadFile] = File(None),
    right_iris: Optional[UploadFile] = File(None)
):
    """
    Analyze iris images using a specific doctor's methodology.

    - doctor: "peczely", "jensen", or "morse"
    - Upload one or both iris images
    - Returns analysis from the specified doctor's perspective
    """
    if not left_iris and not right_iris:
        raise HTTPException(status_code=400, detail="At least one iris image is required")

    if doctor.lower() not in ["peczely", "jensen", "morse"]:
        raise HTTPException(status_code=400, detail="Doctor must be 'peczely', 'jensen', or 'morse'")

    left_features = None
    right_features = None

    if left_iris:
        left_data = await left_iris.read()
        left_features = await image_processor.process_image(left_data, "left")

    if right_iris:
        right_data = await right_iris.read()
        right_features = await image_processor.process_image(right_data, "right")

    # Run analysis with specified doctor agent
    analysis_result = agent_manager.analyze_single(
        doctor=doctor,
        left_iris_features=left_features,
        right_iris_features=right_features,
        patient_name=patient_name,
        notes=notes
    )

    return {
        "patient_name": patient_name,
        "notes": notes,
        "image_analysis": {
            "left_iris": left_features,
            "right_iris": right_features
        },
        "doctor_analysis": analysis_result
    }


@router.post("/process-image")
async def process_image_only(
    eye_side: str = Form(...),
    iris_image: UploadFile = File(...)
):
    """
    Process an iris image without LLM analysis.

    Returns extracted features that can be used for visualization
    or further analysis.
    """
    if eye_side not in ["left", "right"]:
        raise HTTPException(status_code=400, detail="eye_side must be 'left' or 'right'")

    image_data = await iris_image.read()
    features = await image_processor.process_image(image_data, eye_side)

    return {
        "eye_side": eye_side,
        "features": features
    }


@router.post("/annotate-image")
async def get_annotated_image(
    eye_side: str = Form(...),
    iris_image: UploadFile = File(...)
):
    """
    Get an annotated version of the iris image with zones marked.
    """
    if eye_side not in ["left", "right"]:
        raise HTTPException(status_code=400, detail="eye_side must be 'left' or 'right'")

    image_data = await iris_image.read()
    features = await image_processor.process_image(image_data, eye_side)
    annotated = image_processor.create_annotated_image(image_data, features)

    from fastapi.responses import Response
    return Response(content=annotated, media_type="image/png")


@router.post("/preprocess-image")
async def get_preprocessed_image(
    eye_side: str = Form(...),
    iris_image: UploadFile = File(...),
    remove_glare: bool = Form(True),
    enhance: bool = Form(True)
):
    """
    Get a preprocessed version of the iris image with glare removed and contrast enhanced.

    - remove_glare: Remove light reflections using inpainting (default: True)
    - enhance: Apply contrast enhancement (default: True)
    """
    if eye_side not in ["left", "right"]:
        raise HTTPException(status_code=400, detail="eye_side must be 'left' or 'right'")

    import cv2
    import numpy as np

    image_data = await iris_image.read()
    nparr = np.frombuffer(image_data, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if image is None:
        raise HTTPException(status_code=400, detail="Could not decode image")

    # Apply preprocessing
    processed = image_processor.preprocess_iris_image(image, remove_glare, enhance)

    # Encode back to bytes
    _, buffer = cv2.imencode('.png', processed)

    from fastapi.responses import Response
    return Response(content=buffer.tobytes(), media_type="image/png")
