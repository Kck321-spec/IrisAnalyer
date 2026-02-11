# Iridology Analyzer

A web-based iridology analysis application that uses AI/ML for iris image analysis and LLM-powered agents representing three renowned iridology practitioners.

## Doctors/Methodologies

1. **Ignaz von Peczely (1826-1911)** - Father of modern iridology, historical/foundational approach
2. **Bernard Jensen (1908-2001)** - 75 years of research, comprehensive constitutional analysis with 96-zone iris chart
3. **Dr. Robert Morse, ND** - Naturopathic/detoxification approach, emphasis on lymphatic system

## Features

- Upload left and right iris images
- AI-powered iris feature extraction using OpenCV
- Analysis from three different iridology perspectives
- Interactive image viewer with zoom
- Patient record management

## Prerequisites

- Python 3.10+
- Node.js 18+
- Anthropic API key (for Claude)

## Setup

### 1. Clone and Navigate
```bash
cd iridology-analyzer
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your API key
copy .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
```

## Running the Application

### Start Backend (Terminal 1)
```bash
cd backend
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux
uvicorn app.main:app --reload --port 8000
```

### Start Frontend (Terminal 2)
```bash
cd frontend
npm run dev
```

### Access the Application
Open your browser to: http://localhost:5173

## Usage

1. Enter the patient's name
2. Optionally add notes about symptoms or concerns
3. Upload left and/or right iris images (drag & drop or click)
4. Click "Analyze Iris"
5. View analysis from each doctor's perspective using the tabs

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/analysis/analyze` | Analyze with all three doctors |
| POST | `/api/analysis/analyze/{doctor}` | Analyze with specific doctor |
| POST | `/api/analysis/process-image` | Extract features only |
| GET | `/api/patients/` | List all patients |
| POST | `/api/patients/` | Create patient |

## Project Structure

```
iridology-analyzer/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── routers/
│   │   │   ├── analysis.py      # Analysis endpoints
│   │   │   └── patients.py      # Patient management
│   │   ├── services/
│   │   │   ├── image_processor.py  # OpenCV iris analysis
│   │   │   └── llm_agents.py       # Claude-powered agents
│   │   ├── knowledge/
│   │   │   ├── peczely_methodology.md
│   │   │   ├── jensen_methodology.md
│   │   │   ├── jensen_iris_chart.json
│   │   │   └── morse_methodology.md
│   │   └── models/
│   │       └── schemas.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── PatientForm.tsx
│   │   │   ├── ImageUploader.tsx
│   │   │   ├── IrisViewer.tsx
│   │   │   ├── AnalysisPanel.tsx
│   │   │   └── DoctorInsightCard.tsx
│   │   ├── services/
│   │   │   └── api.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   └── package.json
└── README.md
```

## Disclaimer

This tool provides observations based on traditional iridology principles as practiced by the referenced practitioners. It is not intended to diagnose, treat, cure, or prevent any disease or medical condition. Always consult with qualified healthcare professionals for medical advice.

## Knowledge Base Sources

The methodologies implemented are based on:
- Peczely's "Discoveries in the Realms of Nature and Art of Healing" (1880)
- Jensen's "Iridology: The Science and Practice in the Healing Arts"
- Jensen's "Iridology Simplified"
- Dr. Morse's teachings on detoxification and regenerative healing
