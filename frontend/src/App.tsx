import { useState, useCallback } from 'react'
import PatientForm from './components/PatientForm'
import ImageUploader from './components/ImageUploader'
import IrisViewer from './components/IrisViewer'
import AnalysisPanel from './components/AnalysisPanel'
import { analyzeIris } from './services/api'

interface AnalysisResult {
  patient_name: string
  notes: string | null
  image_analysis: {
    left_iris: any | null
    right_iris: any | null
  }
  doctor_analyses: {
    peczely: DoctorAnalysis
    jensen: DoctorAnalysis
    morse: DoctorAnalysis
  }
}

interface DoctorAnalysis {
  doctor_name: string
  methodology: string
  findings: string[]
  organ_correlations: Record<string, string>
  recommendations: string[]
  confidence_notes: string
}

interface SkinColor {
  base: string
  highlight: string
  shadow: string
  deepShadow: string
}

// Default skin tone (neutral)
const defaultSkinColor: SkinColor = {
  base: '#c9a07a',
  highlight: '#ddb896',
  shadow: '#8b6b4a',
  deepShadow: '#5c4530',
}

// Extract skin color from the edges/corners of an eye image
const extractSkinColorFromImage = (imageUrl: string): Promise<SkinColor> => {
  return new Promise((resolve) => {
    const img = new Image()
    img.crossOrigin = 'anonymous'
    img.onload = () => {
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')
      if (!ctx) {
        resolve(defaultSkinColor)
        return
      }

      canvas.width = img.width
      canvas.height = img.height
      ctx.drawImage(img, 0, 0)

      // Sample pixels from corners and edges where skin is likely visible
      const samplePoints = [
        // Top corners
        { x: Math.floor(img.width * 0.05), y: Math.floor(img.height * 0.05) },
        { x: Math.floor(img.width * 0.95), y: Math.floor(img.height * 0.05) },
        // Bottom corners
        { x: Math.floor(img.width * 0.05), y: Math.floor(img.height * 0.95) },
        { x: Math.floor(img.width * 0.95), y: Math.floor(img.height * 0.95) },
        // Mid edges
        { x: Math.floor(img.width * 0.1), y: Math.floor(img.height * 0.5) },
        { x: Math.floor(img.width * 0.9), y: Math.floor(img.height * 0.5) },
        // Upper mid edges
        { x: Math.floor(img.width * 0.15), y: Math.floor(img.height * 0.15) },
        { x: Math.floor(img.width * 0.85), y: Math.floor(img.height * 0.15) },
      ]

      const colors: { r: number; g: number; b: number }[] = []

      samplePoints.forEach((point) => {
        const pixelData = ctx.getImageData(point.x, point.y, 1, 1).data
        // Filter out very dark (likely eyelashes/pupil) or very bright (likely sclera/reflection) pixels
        const brightness = (pixelData[0] + pixelData[1] + pixelData[2]) / 3
        if (brightness > 60 && brightness < 220) {
          colors.push({ r: pixelData[0], g: pixelData[1], b: pixelData[2] })
        }
      })

      if (colors.length === 0) {
        resolve(defaultSkinColor)
        return
      }

      // Average the sampled colors
      const avgColor = colors.reduce(
        (acc, c) => ({ r: acc.r + c.r / colors.length, g: acc.g + c.g / colors.length, b: acc.b + c.b / colors.length }),
        { r: 0, g: 0, b: 0 }
      )

      // Create color variations for the nose
      const toHex = (r: number, g: number, b: number) =>
        `#${Math.round(r).toString(16).padStart(2, '0')}${Math.round(g).toString(16).padStart(2, '0')}${Math.round(b).toString(16).padStart(2, '0')}`

      resolve({
        base: toHex(avgColor.r, avgColor.g, avgColor.b),
        highlight: toHex(
          Math.min(255, avgColor.r * 1.15),
          Math.min(255, avgColor.g * 1.12),
          Math.min(255, avgColor.b * 1.1)
        ),
        shadow: toHex(avgColor.r * 0.7, avgColor.g * 0.65, avgColor.b * 0.6),
        deepShadow: toHex(avgColor.r * 0.45, avgColor.g * 0.4, avgColor.b * 0.35),
      })
    }
    img.onerror = () => resolve(defaultSkinColor)
    img.src = imageUrl
  })
}

function App() {
  const [patientName, setPatientName] = useState('')
  const [notes, setNotes] = useState('')
  const [leftIris, setLeftIris] = useState<File | null>(null)
  const [rightIris, setRightIris] = useState<File | null>(null)
  const [leftPreview, setLeftPreview] = useState<string | null>(null)
  const [rightPreview, setRightPreview] = useState<string | null>(null)
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [skinColor, setSkinColor] = useState<SkinColor>(defaultSkinColor)

  const updateSkinColor = useCallback(async (imageUrl: string) => {
    const detectedColor = await extractSkinColorFromImage(imageUrl)
    setSkinColor(detectedColor)
  }, [])

  const handleLeftIrisUpload = (file: File) => {
    setLeftIris(file)
    const previewUrl = URL.createObjectURL(file)
    setLeftPreview(previewUrl)
    updateSkinColor(previewUrl)
  }

  const handleRightIrisUpload = (file: File) => {
    setRightIris(file)
    const previewUrl = URL.createObjectURL(file)
    setRightPreview(previewUrl)
    updateSkinColor(previewUrl)
  }

  const handleAnalyze = async () => {
    if (!patientName.trim()) {
      setError('Please enter a patient name')
      return
    }
    if (!leftIris && !rightIris) {
      setError('Please upload at least one iris image')
      return
    }

    setError(null)
    setIsAnalyzing(true)

    try {
      const result = await analyzeIris(patientName, notes, leftIris, rightIris)
      setAnalysisResult(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed')
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleClear = () => {
    setPatientName('')
    setNotes('')
    setLeftIris(null)
    setRightIris(null)
    setLeftPreview(null)
    setRightPreview(null)
    setAnalysisResult(null)
    setError(null)
    setSkinColor(defaultSkinColor)
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="iris-gradient py-6 px-8 shadow-lg">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-3xl font-bold">Iridology Analyzer</h1>
          <p className="text-blue-200 mt-1">
            Analysis based on Peczely, Jensen & Morse methodologies
          </p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-8 px-4">
        {/* Patient Info Section */}
        <div className="mb-6">
          <div className="bg-gray-800 rounded-lg p-6 max-w-md mx-auto">
            <h2 className="text-xl font-semibold mb-4">Patient Information</h2>
            <PatientForm
              patientName={patientName}
              setPatientName={setPatientName}
              notes={notes}
              setNotes={setNotes}
            />
          </div>
        </div>

        {/* Iris Upload Section */}
        <div className="flex justify-center gap-8 mb-8">
          {/* Right Iris Upload - shown on left (anatomically correct view) */}
          <div className="bg-gray-800 rounded-lg p-6 w-72">
            <h2 className="text-xl font-semibold mb-4 text-center">Right Iris (OD)</h2>
            <ImageUploader
              onUpload={handleRightIrisUpload}
              preview={rightPreview}
              label="Right Eye"
            />
          </div>

          {/* Left Iris Upload - shown on right (anatomically correct view) */}
          <div className="bg-gray-800 rounded-lg p-6 w-72">
            <h2 className="text-xl font-semibold mb-4 text-center">Left Iris (OS)</h2>
            <ImageUploader
              onUpload={handleLeftIrisUpload}
              preview={leftPreview}
              label="Left Eye"
            />
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-900/50 border border-red-500 text-red-200 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex justify-center gap-4 mb-8">
          <button
            onClick={handleAnalyze}
            disabled={isAnalyzing}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:cursor-not-allowed px-8 py-3 rounded-lg font-semibold transition-colors"
          >
            {isAnalyzing ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Analyzing...
              </span>
            ) : (
              'Analyze Iris'
            )}
          </button>
          <button
            onClick={handleClear}
            className="bg-gray-700 hover:bg-gray-600 px-8 py-3 rounded-lg font-semibold transition-colors"
          >
            Clear All
          </button>
        </div>

        {/* Iris Viewer */}
        {(leftPreview || rightPreview) && (
          <div className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">Iris Images</h2>
            <IrisViewer leftImage={leftPreview} rightImage={rightPreview} />
          </div>
        )}

        {/* Iris Reference Chart - always visible */}
        <div className="mb-8">
          <img
            src="/images/iris-chart.png.png"
            alt="Iridology Reference Chart - Right and Left Iris zones"
            className="w-full h-auto rounded-lg"
          />
        </div>

        {/* Analysis Results */}
        {analysisResult && (
          <div className="mt-8">
            <h2 className="text-2xl font-semibold mb-4">
              Analysis Results for {analysisResult.patient_name}
            </h2>
            <AnalysisPanel analyses={analysisResult.doctor_analyses} />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 py-6 px-8 mt-12">
        <div className="max-w-7xl mx-auto text-center text-gray-400">
          <p className="mb-2">
            <strong>Disclaimer:</strong> This tool provides observations based on traditional iridology principles.
            It is not intended to diagnose, treat, or cure any medical condition.
          </p>
          <p>
            Based on the work of Ignaz von Peczely, Bernard Jensen, and Dr. Robert Morse
          </p>
        </div>
      </footer>
    </div>
  )
}

export default App
