"""
Iridology Analyzer - FastAPI Backend

Main application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .routers import analysis_router, patients_router

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Iridology Analyzer API",
    description="""
    An iridology analysis system based on the methodologies of three renowned practitioners:

    - **Ignaz von Peczely (1826-1911)**: Father of modern iridology, historical approach
    - **Bernard Jensen (1908-2001)**: 75 years of research, comprehensive constitutional analysis
    - **Dr. Robert Morse, ND**: Naturopathic/detoxification focus, emphasis on lymphatic system

    Upload iris images and receive analysis from each doctor's unique perspective.
    """,
    version="1.0.0"
)

# Configure CORS for frontend
import os
allowed_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "https://iris-analyzer.vercel.app",
    "https://iris-analyzer-kck321-specs-projects.vercel.app",
]
# Add production frontend URL from environment
if os.getenv("FRONTEND_URL"):
    allowed_origins.append(os.getenv("FRONTEND_URL"))
# Allow all origins in production if explicitly set (for flexibility)
if os.getenv("ALLOW_ALL_ORIGINS", "").lower() == "true":
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(analysis_router)
app.include_router(patients_router)


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "Iridology Analyzer API",
        "version": "1.0.0",
        "doctors": [
            {
                "name": "Ignaz von Peczely",
                "years": "1826-1911",
                "focus": "Historical/Foundational Iridology"
            },
            {
                "name": "Bernard Jensen",
                "years": "1908-2001",
                "focus": "Comprehensive Constitutional Analysis"
            },
            {
                "name": "Dr. Robert Morse, ND",
                "years": "Active",
                "focus": "Naturopathic/Detoxification Approach"
            }
        ],
        "endpoints": {
            "analyze_all": "POST /api/analysis/analyze",
            "analyze_single": "POST /api/analysis/analyze/{doctor}",
            "process_image": "POST /api/analysis/process-image",
            "patients": "/api/patients/"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
