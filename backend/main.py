from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import shutil
import subprocess
import json
import os

app = FastAPI(title="PII Redaction API", version="1.0.0")

# ============================
# 🔧 CORS Setup
# ============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend origin later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================
# 📁 Directory Setup
# ============================
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
COMPARED_DIR = OUTPUT_DIR / "comparisons"

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
COMPARED_DIR.mkdir(exist_ok=True)

# ============================
# 🏠 Health Check
# ============================
@app.get("/")
def read_root():
    return {"message": "✅ PII Redaction API is running!"}

# ============================
# 📤 Upload + Redact Endpoint
# ============================
@app.post("/upload-and-redact/")
async def upload_and_redact(file: UploadFile = File(...)):
    """
    Uploads a file and performs PII redaction using Redactopii engine
    """
    try:
        # Save uploaded file
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Define report output path
        report_path = OUTPUT_DIR / f"{Path(file.filename).stem}_report.json"

        # Construct command to trigger your redaction script
        cmd = [
            "python",
            "Redactopii/redactopii.py",
            "--input", str(file_path),
            "--report", str(report_path)
        ]

        # Execute redaction engine
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Redaction failed: {result.stderr or result.stdout}"
            )

        # Load the generated report (if any)
        if report_path.exists():
            with open(report_path, "r", encoding="utf-8") as f:
                report_data = json.load(f)
        else:
            report_data = {"status": "unknown", "message": "No report generated."}

        # Locate redacted file (could be in /outputs/redacted or /outputs/comparisons)
        redacted_path = None
        for subdir in ["redacted", "comparisons", "compared"]:
            candidate = OUTPUT_DIR / subdir / file.filename
            if candidate.exists():
                redacted_path = candidate
                break

        return JSONResponse({
            "status": "success",
            "input_file": file.filename,
            "report": report_data,
            "redacted_file_found": bool(redacted_path),
            "redacted_file_path": str(redacted_path) if redacted_path else None
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================
# 📥 Download Endpoint
# ============================
@app.get("/download-redacted/{filename}")
async def download_redacted(filename: str):
    """
    Download the redacted file by filename
    """
    search_dirs = [OUTPUT_DIR / "redacted", OUTPUT_DIR / "comparisons", OUTPUT_DIR / "compared"]

    file_path = None
    for directory in search_dirs:
        candidate = directory / filename
        if candidate.exists():
            file_path = candidate
            break

    if not file_path:
        raise HTTPException(status_code=404, detail="Redacted file not found")

    return FileResponse(
        path=file_path,
        filename=f"redacted_{filename}",
        media_type="application/octet-stream"
    )

# ============================
# 📂 List All Output Files
# ============================
@app.get("/list-outputs/")
def list_outputs():
    """
    Lists all available redacted or comparison files
    """
    output_files = []
    for subdir in ["redacted", "comparisons", "compared"]:
        path = OUTPUT_DIR / subdir
        if path.exists():
            output_files.extend([f.name for f in path.iterdir() if f.is_file()])

    return {"files": sorted(output_files)}

# ============================
# 🚀 Run Server (Dev)
# ============================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
