import axios from 'axios'

// Use environment variable for API URL, fallback to relative path for development
const API_BASE = import.meta.env.VITE_API_URL || '/api'

export interface AnalysisResult {
  patient_name: string
  notes: string | null
  image_analysis: {
    left_iris: IrisFeatures | null
    right_iris: IrisFeatures | null
  }
  doctor_analyses: {
    peczely: DoctorAnalysis
    jensen: DoctorAnalysis
    morse: DoctorAnalysis
  }
}

export interface IrisFeatures {
  eye_side: string
  dominant_color: string
  color_distribution: Record<string, any>
  pupil_size_ratio: number
  collarette_regularity: number
  detected_markings: Marking[]
  zone_analysis: Record<string, ZoneInfo>
  nerve_rings_count: number
  radial_furrows: Furrow[]
  overall_density: string
  lymphatic_signs: LymphaticSigns
  brightness_analysis: BrightnessInfo
}

export interface Marking {
  type: string
  position: { x: number; y: number }
  clock_position: string
  zone: string
  size: string
  intensity: string
}

export interface ZoneInfo {
  mean_brightness: number
  variability: number
  condition: string
  notes: string
}

export interface Furrow {
  angle: number
  clock_position: string
  strength: number
}

export interface LymphaticSigns {
  rosary_beads_count: number
  rosary_present: boolean
  scurf_rim_present: boolean
  lymphatic_congestion_level: string
}

export interface BrightnessInfo {
  mean: number
  std: number
  min: number
  max: number
  overall_assessment: string
}

export interface DoctorAnalysis {
  doctor_name: string
  methodology: string
  findings: string[]
  organ_correlations: Record<string, string>
  recommendations: string[]
  confidence_notes: string
}

export async function analyzeIris(
  patientName: string,
  notes: string | null,
  leftIris: File | null,
  rightIris: File | null
): Promise<AnalysisResult> {
  const formData = new FormData()
  formData.append('patient_name', patientName)

  if (notes) {
    formData.append('notes', notes)
  }

  if (leftIris) {
    formData.append('left_iris', leftIris)
  }

  if (rightIris) {
    formData.append('right_iris', rightIris)
  }

  const response = await axios.post(`${API_BASE}/analysis/analyze`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })

  return response.data
}

export async function analyzeIrisSingleDoctor(
  doctor: 'peczely' | 'jensen' | 'morse',
  patientName: string,
  notes: string | null,
  leftIris: File | null,
  rightIris: File | null
): Promise<{
  patient_name: string
  notes: string | null
  image_analysis: {
    left_iris: IrisFeatures | null
    right_iris: IrisFeatures | null
  }
  doctor_analysis: DoctorAnalysis
}> {
  const formData = new FormData()
  formData.append('patient_name', patientName)

  if (notes) {
    formData.append('notes', notes)
  }

  if (leftIris) {
    formData.append('left_iris', leftIris)
  }

  if (rightIris) {
    formData.append('right_iris', rightIris)
  }

  const response = await axios.post(`${API_BASE}/analysis/analyze/${doctor}`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })

  return response.data
}

export async function processImageOnly(
  eyeSide: 'left' | 'right',
  irisImage: File
): Promise<{ eye_side: string; features: IrisFeatures }> {
  const formData = new FormData()
  formData.append('eye_side', eyeSide)
  formData.append('iris_image', irisImage)

  const response = await axios.post(`${API_BASE}/analysis/process-image`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })

  return response.data
}

export async function getAnnotatedImage(
  eyeSide: 'left' | 'right',
  irisImage: File
): Promise<Blob> {
  const formData = new FormData()
  formData.append('eye_side', eyeSide)
  formData.append('iris_image', irisImage)

  const response = await axios.post(`${API_BASE}/analysis/annotate-image`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    responseType: 'blob',
  })

  return response.data
}

export async function getPreprocessedImage(
  eyeSide: 'left' | 'right',
  irisImage: File,
  removeGlare: boolean = true,
  enhance: boolean = true
): Promise<Blob> {
  const formData = new FormData()
  formData.append('eye_side', eyeSide)
  formData.append('iris_image', irisImage)
  formData.append('remove_glare', String(removeGlare))
  formData.append('enhance', String(enhance))

  const response = await axios.post(`${API_BASE}/analysis/preprocess-image`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    responseType: 'blob',
  })

  return response.data
}

export async function getCroppedIris(irisImage: File): Promise<Blob> {
  const formData = new FormData()
  formData.append('iris_image', irisImage)

  const response = await axios.post(`${API_BASE}/analysis/crop-iris`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    responseType: 'blob',
  })

  return response.data
}

// Patient management
export interface Patient {
  id: number
  name: string
  notes: string | null
  created_at: string
}

export async function getPatients(): Promise<Patient[]> {
  const response = await axios.get(`${API_BASE}/patients/`)
  return response.data
}

export async function getPatient(id: number): Promise<Patient> {
  const response = await axios.get(`${API_BASE}/patients/${id}`)
  return response.data
}

export async function createPatient(name: string, notes?: string): Promise<Patient> {
  const response = await axios.post(`${API_BASE}/patients/`, { name, notes })
  return response.data
}

export async function updatePatient(id: number, name: string, notes?: string): Promise<Patient> {
  const response = await axios.put(`${API_BASE}/patients/${id}`, { name, notes })
  return response.data
}

export async function deletePatient(id: number): Promise<void> {
  await axios.delete(`${API_BASE}/patients/${id}`)
}
