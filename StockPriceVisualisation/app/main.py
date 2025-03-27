from fastapi import FastAPI
from app.services.dataIntegrationService import router as data_integration_router
from app.services.dataStorageService import router as data_storage_router
from app.services.dataAnalysisService import router as data_analysis_router
from app.database import initialize_database
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

import uvicorn
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

app = FastAPI(title="Ksenija Stock Price Visualisation")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the database
initialize_database()

# Include routers for different services
app.include_router(data_integration_router, prefix="/integration", tags=["Data Integration"])
app.include_router(data_storage_router, prefix="/storage", tags=["Data Storage"])
app.include_router(data_analysis_router, prefix="/analysis", tags=["Data Analysis"])

# Mount the public folder to serve static files
app.mount("/public", StaticFiles(directory="app/public"), name="public")

# Serve the index.html file at the root
@app.get("/")
async def serve_index():
    return FileResponse("app/public/index.html")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)