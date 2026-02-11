from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PatientCreate(BaseModel):
    name: str
    notes: Optional[str] = None


class Patient(BaseModel):
    id: int
    name: str
    notes: Optional[str] = None
    created_at: datetime


class IrisFeatures(BaseModel):
    """Extracted features from iris image analysis"""
    eye_side: str  # "left" or "right"
    dominant_color: str
    color_distribution: dict
    pupil_size_ratio: float
    collarette_regularity: float
    detected_markings: List[dict]  # lacunae, crypts, pigment spots, etc.
    zone_analysis: dict  # Analysis by iris zones
    nerve_rings_count: int
    radial_furrows: List[dict]
    overall_density: str  # "silk", "linen", "hessian", "net"


class DoctorAnalysis(BaseModel):
    """Analysis from a single doctor agent"""
    doctor_name: str
    methodology: str
    findings: List[str]
    organ_correlations: dict
    recommendations: List[str]
    confidence_notes: str


class AnalysisResult(BaseModel):
    """Complete analysis result"""
    id: int
    patient_id: int
    left_iris_features: Optional[IrisFeatures]
    right_iris_features: Optional[IrisFeatures]
    peczely_analysis: DoctorAnalysis
    jensen_analysis: DoctorAnalysis
    morse_analysis: DoctorAnalysis
    created_at: datetime


class AnalysisRequest(BaseModel):
    patient_name: str
    notes: Optional[str] = None
