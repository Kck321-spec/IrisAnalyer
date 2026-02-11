"""
Patients Router

Handles patient record management.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime
import json
from pathlib import Path

from ..models.schemas import PatientCreate, Patient

router = APIRouter(prefix="/api/patients", tags=["patients"])

# Simple file-based storage for patients
PATIENTS_FILE = Path(__file__).parent.parent.parent / "data" / "patients.json"


def _ensure_data_dir():
    """Ensure the data directory exists."""
    PATIENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not PATIENTS_FILE.exists():
        with open(PATIENTS_FILE, "w") as f:
            json.dump({"patients": [], "next_id": 1}, f)


def _load_patients() -> dict:
    """Load patients from file."""
    _ensure_data_dir()
    with open(PATIENTS_FILE, "r") as f:
        return json.load(f)


def _save_patients(data: dict):
    """Save patients to file."""
    _ensure_data_dir()
    with open(PATIENTS_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


@router.get("/", response_model=List[Patient])
async def list_patients():
    """Get all patients."""
    data = _load_patients()
    return [
        Patient(
            id=p["id"],
            name=p["name"],
            notes=p.get("notes"),
            created_at=datetime.fromisoformat(p["created_at"])
        )
        for p in data["patients"]
    ]


@router.get("/{patient_id}", response_model=Patient)
async def get_patient(patient_id: int):
    """Get a specific patient by ID."""
    data = _load_patients()
    for p in data["patients"]:
        if p["id"] == patient_id:
            return Patient(
                id=p["id"],
                name=p["name"],
                notes=p.get("notes"),
                created_at=datetime.fromisoformat(p["created_at"])
            )
    raise HTTPException(status_code=404, detail="Patient not found")


@router.post("/", response_model=Patient)
async def create_patient(patient: PatientCreate):
    """Create a new patient."""
    data = _load_patients()

    new_patient = {
        "id": data["next_id"],
        "name": patient.name,
        "notes": patient.notes,
        "created_at": datetime.now().isoformat()
    }

    data["patients"].append(new_patient)
    data["next_id"] += 1
    _save_patients(data)

    return Patient(
        id=new_patient["id"],
        name=new_patient["name"],
        notes=new_patient["notes"],
        created_at=datetime.fromisoformat(new_patient["created_at"])
    )


@router.put("/{patient_id}", response_model=Patient)
async def update_patient(patient_id: int, patient: PatientCreate):
    """Update an existing patient."""
    data = _load_patients()

    for i, p in enumerate(data["patients"]):
        if p["id"] == patient_id:
            data["patients"][i]["name"] = patient.name
            data["patients"][i]["notes"] = patient.notes
            _save_patients(data)

            return Patient(
                id=p["id"],
                name=patient.name,
                notes=patient.notes,
                created_at=datetime.fromisoformat(p["created_at"])
            )

    raise HTTPException(status_code=404, detail="Patient not found")


@router.delete("/{patient_id}")
async def delete_patient(patient_id: int):
    """Delete a patient."""
    data = _load_patients()

    for i, p in enumerate(data["patients"]):
        if p["id"] == patient_id:
            del data["patients"][i]
            _save_patients(data)
            return {"message": "Patient deleted successfully"}

    raise HTTPException(status_code=404, detail="Patient not found")
