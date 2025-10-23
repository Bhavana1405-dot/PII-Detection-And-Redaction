from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import shutil
import subprocess
import json
import os
import uuid
from datetime import datetime

app = FastAPI(title="PII Detection & Redaction API", version="2.0.0")

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
REPORTS_DIR = OUTPUT_DIR / "reports"
REDACTED_DIR = OUTPUT_DIR / "redacted"
COMPARED_DIR = OUTPUT_DIR / "comparisons"

# Create all required directories
for directory in [UPLOAD_DIR, OUTPUT_DIR, REPORTS_DIR, REDACTED_DIR, COMPARED_DIR]:
    directory.mkdir(exist_ok=True)

# ============================
# 🏠 Health Check
# ============================
@app.get("/")
def read_root():
    return {
        "message": "✅ PII Detection & Redaction API is running!",
        "version": "2.0.0",
        "endpoints": {
            "detect": "/detect-pii/",
            "redact": "/redact-pii/",
            "download": "/download-redacted/{filename}",
            "download_report": "/download-report/{filename}",
            "list": "/list-outputs/"
        }
    }

# ============================
# 🔍 ROUTE 1: Detect PII Only
# ============================
@app.post("/detect-pii/")
async def detect_pii(file: UploadFile = File(...)):
    """
    Detects PII in uploaded file using Octopii scanner.
    Returns detection report without redacting the file.
    
    Returns:
    - Detection report with all found PIIs
    - Locations of PIIs (bounding boxes or text offsets)
    - PII classification and confidence scores
    """
    try:
        # Generate unique identifier for this scan
        scan_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save uploaded file with unique name
        file_stem = Path(file.filename).stem
        file_ext = Path(file.filename).suffix
        unique_filename = f"{file_stem}_{scan_id}{file_ext}"
        file_path = UPLOAD_DIR / unique_filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Define report output path
        report_filename = f"{file_stem}_{timestamp}_{scan_id}_report.json"
        report_path = REPORTS_DIR / report_filename

        # Run Octopii detection
        octopii_script = BASE_DIR / "Octopii" / "octopii.py"
        
        cmd = [
            "python",
            str(octopii_script),
            str(file_path)
        ]

        print(f"[INFO] Running detection: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=BASE_DIR / "Octopii")

        if result.returncode != 0:
            error_msg = result.stderr or result.stdout
            print(f"[ERROR] Octopii failed: {error_msg}")
            raise HTTPException(
                status_code=500,
                detail=f"PII detection failed: {error_msg}"
            )

        # Read the generated output.json from Octopii directory
        octopii_output = BASE_DIR / "Octopii" / "output.json"
        
        if not octopii_output.exists():
            raise HTTPException(
                status_code=500,
                detail="Detection completed but no report was generated"
            )

        # Load detection results
        with open(octopii_output, "r", encoding="utf-8") as f:
            detection_data = json.load(f)

        # Handle batch reports (array) or single report (dict)
        if isinstance(detection_data, list):
            # Find matching report
            report_entry = None
            for entry in detection_data:
                if file_path.name in entry.get("file_path", ""):
                    report_entry = entry
                    break
            
            if not report_entry:
                report_entry = detection_data[-1]  # Use last entry as fallback
        else:
            report_entry = detection_data

        # Save report to our reports directory
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_entry, f, indent=2)

        # Count detected PIIs
        pii_summary = {
            "emails": len(report_entry.get("emails", [])),
            "phone_numbers": len(report_entry.get("phone_numbers", [])),
            "identifiers": len(report_entry.get("identifiers", [])),
            "addresses": len(report_entry.get("addresses", [])),
        }
        total_pii = sum(pii_summary.values())

        # Prepare response
        response_data = {
            "status": "success",
            "scan_id": scan_id,
            "timestamp": timestamp,
            "input_file": file.filename,
            "uploaded_as": unique_filename,
            "report_file": report_filename,
            "detection_summary": {
                "total_pii_found": total_pii,
                "breakdown": pii_summary,
                "pii_class": report_entry.get("pii_class"),
                "confidence_score": report_entry.get("score"),
                "country_of_origin": report_entry.get("country_of_origin"),
                "contains_faces": report_entry.get("faces", 0) > 0
            },
            "detected_pii": {
                "emails": report_entry.get("emails", []),
                "phone_numbers": report_entry.get("phone_numbers", []),
                "identifiers": report_entry.get("identifiers", []),
                "addresses": report_entry.get("addresses", [])
            },
            "pii_locations": report_entry.get("pii_with_locations", {}),
            "full_report": report_entry
        }

        return JSONResponse(content=response_data)

    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Detection process failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during PII detection: {str(e)}"
        )

# ============================
# 🔒 ROUTE 2: Redact PII
# ============================
@app.post("/redact-pii/")
async def redact_pii(
    file: UploadFile = File(...),
    report_filename: str = Form(None),
    method: str = Form("blur")
):
    """
    Redacts PII from uploaded file using detection report.
    
    Parameters:
    - file: The file to redact
    - report_filename: (Optional) Name of existing detection report
                      If not provided, will run detection first
    - method: Redaction method - 'blur', 'blackbox', or 'pixelate' (default: blur)
    
    Returns:
    - Redacted file path
    - Redaction statistics
    - Comparison visualization (if applicable)
    """
    try:
        # Generate unique identifier
        redact_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save uploaded file
        file_stem = Path(file.filename).stem
        file_ext = Path(file.filename).suffix
        unique_filename = f"{file_stem}_{redact_id}{file_ext}"
        file_path = UPLOAD_DIR / unique_filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Check if report exists or need to run detection
        if report_filename:
            report_path = REPORTS_DIR / report_filename
            if not report_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"Report file '{report_filename}' not found. Run /detect-pii/ first."
                )
        else:
            # Run detection first
            print("[INFO] No report provided, running detection first...")
            
            octopii_script = BASE_DIR / "Octopii" / "octopii.py"
            cmd = ["python", str(octopii_script), str(file_path)]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=BASE_DIR / "Octopii")
            
            if result.returncode != 0:
                raise HTTPException(
                    status_code=500,
                    detail=f"PII detection failed: {result.stderr or result.stdout}"
                )

            # Load generated report
            octopii_output = BASE_DIR / "Octopii" / "output.json"
            with open(octopii_output, "r", encoding="utf-8") as f:
                detection_data = json.load(f)
            
            # Save report
            report_filename = f"{file_stem}_{timestamp}_{redact_id}_report.json"
            report_path = REPORTS_DIR / report_filename
            
            if isinstance(detection_data, list):
                report_entry = detection_data[-1]
            else:
                report_entry = detection_data
            
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report_entry, f, indent=2)

        # Run Redactopii
        redactopii_script = BASE_DIR / "Redactopii" / "redactopii.py"
        
        cmd = [
            "python",
            str(redactopii_script),
            "--input", str(file_path),
            "--report", str(report_path),
            "--method", method,
            "--output-dir", str(OUTPUT_DIR)
        ]

        print(f"[INFO] Running redaction: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Log the output for debugging
        if result.stdout:
            print(f"[DEBUG] Stdout: {result.stdout[:500]}")
        if result.stderr:
            print(f"[DEBUG] Stderr: {result.stderr[:500]}")

        # Check for actual errors (not just warnings in stderr)
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout
            
            # Check if redaction actually succeeded despite warnings
            if "Saved redacted" in error_msg or "SUCCESS" in error_msg:
                print(f"[INFO] Redaction completed with warnings")
                print(f"[WARN] Warnings: {error_msg[:500]}...")  # Log first 500 chars
            else:
                print(f"[ERROR] Redactopii failed: {error_msg}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Redaction failed: {error_msg}"
                )

        # Find redacted file - check multiple patterns
        redacted_path = None
        search_dirs = [REDACTED_DIR, COMPARED_DIR, OUTPUT_DIR / "compared"]
        
        # Try multiple search patterns
        search_patterns = [
            f"*{file_stem}*{file_ext}",
            f"*{file_stem}*redacted*{file_ext}",
            f"*{unique_filename.replace(file_ext, '')}*{file_ext}",
            f"*redacted*{file_ext}"
        ]
        
        for directory in search_dirs:
            if not directory.exists():
                continue
            for pattern in search_patterns:
                candidates = list(directory.glob(pattern))
                if candidates:
                    # Get the most recently created file
                    redacted_path = max(candidates, key=lambda p: p.stat().st_mtime)
                    print(f"[INFO] Found redacted file: {redacted_path}")
                    break
            if redacted_path:
                break

        if not redacted_path:
            # List what files ARE in the output directories for debugging
            available_files = []
            for directory in search_dirs:
                if directory.exists():
                    available_files.extend([f.name for f in directory.iterdir() if f.is_file()])
            
            error_detail = "Redaction completed but output file not found."
            if available_files:
                error_detail += f" Available files: {', '.join(available_files[:5])}"
            
            raise HTTPException(
                status_code=500,
                detail=error_detail
            )

        # Load report for statistics
        with open(report_path, "r", encoding="utf-8") as f:
            report_data = json.load(f)

        # Calculate statistics
        pii_summary = {
            "emails": len(report_data.get("emails", [])),
            "phone_numbers": len(report_data.get("phone_numbers", [])),
            "identifiers": len(report_data.get("identifiers", [])),
            "addresses": len(report_data.get("addresses", [])),
        }
        total_redacted = sum(pii_summary.values())

        # Prepare response
        response_data = {
            "status": "success",
            "redact_id": redact_id,
            "timestamp": timestamp,
            "input_file": file.filename,
            "redacted_file": redacted_path.name,
            "report_used": report_filename,
            "redaction_method": method,
            "redaction_summary": {
                "total_entities_redacted": total_redacted,
                "breakdown": pii_summary
            },
            "download_url": f"/download-redacted/{redacted_path.name}",
            "report_url": f"/download-report/{report_filename}"
        }

        return JSONResponse(content=response_data)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during PII redaction: {str(e)}"
        )

# ============================
# 📥 Download Redacted File
# ============================
@app.get("/download-redacted/{filename}")
async def download_redacted(filename: str):
    """
    Download the redacted file by filename
    """
    search_dirs = [REDACTED_DIR, COMPARED_DIR, OUTPUT_DIR / "compared"]

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
# 📥 Download Detection Report
# ============================
@app.get("/download-report/{filename}")
async def download_report(filename: str):
    """
    Download the detection report JSON file
    """
    report_path = REPORTS_DIR / filename
    
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")

    return FileResponse(
        path=report_path,
        filename=filename,
        media_type="application/json"
    )

# ============================
# 📂 List All Outputs
# ============================
@app.get("/list-outputs/")
def list_outputs():
    """
    Lists all available files (reports, redacted files, etc.)
    """
    outputs = {
        "reports": [],
        "redacted_files": [],
        "comparisons": []
    }
    
    # List reports
    if REPORTS_DIR.exists():
        outputs["reports"] = [f.name for f in REPORTS_DIR.iterdir() if f.is_file()]
    
    # List redacted files
    if REDACTED_DIR.exists():
        outputs["redacted_files"] = [f.name for f in REDACTED_DIR.iterdir() if f.is_file()]
    
    # List comparison files
    if COMPARED_DIR.exists():
        outputs["comparisons"] = [f.name for f in COMPARED_DIR.iterdir() if f.is_file()]

    return outputs

# ============================
# 🗑️ Cleanup Endpoint (Optional)
# ============================
@app.delete("/cleanup/")
def cleanup_files(older_than_hours: int = 24):
    """
    Clean up old uploaded files and outputs
    """
    import time
    from datetime import timedelta
    
    cutoff_time = time.time() - (older_than_hours * 3600)
    deleted_count = 0
    
    for directory in [UPLOAD_DIR, REPORTS_DIR, REDACTED_DIR, COMPARED_DIR]:
        if not directory.exists():
            continue
            
        for file_path in directory.iterdir():
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    deleted_count += 1
                except Exception as e:
                    print(f"[WARN] Could not delete {file_path}: {e}")
    
    return {
        "status": "success",
        "deleted_files": deleted_count,
        "cutoff_hours": older_than_hours
    }

# ============================
# 🚀 Run Server (Dev)
# ============================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)