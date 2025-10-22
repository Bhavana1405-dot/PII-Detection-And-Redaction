# =============================================================================
# FILE: Redactopii/core/redaction_engine.py  
# DESCRIPTION: FIXED - Precise redaction that only targets PII, not entire blocks
# =============================================================================

"""
Core redaction engine with PRECISE PII-only redaction
CRITICAL FIX: Only redact the exact PII text, not surrounding content
"""
import logging
import json
import os
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

from .models import PIIEntity, RedactionResult, RedactionMethod, BoundingBox, PIIType
from .config import RedactionConfig

try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False


class RedactionEngine:
    """Main orchestrator for redaction operations"""
    
    def __init__(self, config: Optional[RedactionConfig] = None):
        self.config = config or RedactionConfig()
        self.logger = self._setup_logging()
        self.audit_log: List[Dict] = []

        # Setup output directories
        base = Path(self.config.get("output_base_dir", "./outputs"))
        self.output_base = base
        self.output_dirs = {
            "redacted": base / "redacted",
            "reports": base / "reports",
            "audit_logs": base / "audit_logs",
            "comparisons": base / "comparisons"
        }

        for p in self.output_dirs.values():
            p.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Initialized RedactionEngine; outputs -> {self.output_base}")

    def _setup_logging(self) -> logging.Logger:
        level = self.config.get("log_level", "INFO")
        logger = logging.getLogger("RedactionEngine")
        if not logger.handlers:
            handler = logging.StreamHandler()
            fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(fmt)
            logger.addHandler(handler)
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        return logger

    def _calculate_precise_bbox(self, pii_value: str, location: Dict, image_shape: tuple) -> Optional[Dict]:
        """
        Calculate precise bounding box that ONLY covers the PII value
        Adds minimal padding instead of using full OCR word boxes
        """
        try:
            x = int(location.get("x", 0))
            y = int(location.get("y", 0))
            w = int(location.get("width", 0))
            h = int(location.get("height", 0))
            
            if w <= 0 or h <= 0:
                return None
            
            # CRITICAL FIX: Add minimal padding only (5 pixels)
            padding = 10
            
            # Clamp to image bounds
            img_height, img_width = image_shape[:2]
            
            x = max(0, min(x - padding, img_width - 1))
            y = max(0, min(y - padding, img_height - 1))
            w = min(w + 2*padding, img_width - x)
            h = min(h + 2*padding, img_height - y)
            
            if w <= 0 or h <= 0:
                return None
            
            return {"x": x, "y": y, "width": w, "height": h}
            
        except Exception as e:
            self.logger.error(f"Error calculating bbox: {e}")
            return None

    def _apply_redaction_to_roi(self, roi, method: str) -> np.ndarray:
        """Apply redaction method to region of interest"""
        if method == "blur":
            kernel = self.config.get("blur_intensity", 25)
            if kernel % 2 == 0:
                kernel += 1
            return cv2.GaussianBlur(roi, (kernel, kernel), 0)
        
        elif method == "blackbox":
            return np.zeros_like(roi)
        
        elif method == "pixelate":
            block_size = self.config.get("pixelate_block_size", 15)
            h, w = roi.shape[:2]
            
            # Resize down then up for pixelation
            small_h = max(1, h // block_size)
            small_w = max(1, w // block_size)
            
            small = cv2.resize(roi, (small_w, small_h), interpolation=cv2.INTER_LINEAR)
            return cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
        
        else:
            # Default to blur
            return cv2.GaussianBlur(roi, (25, 25), 0)

    def process_octopii_report(self, report: Dict, source_file: Optional[str] = None) -> Dict:
        """Process Octopii report and redact PII with PRECISE boundaries"""
        from integrations.octopii_adapter import OctopiiAdapter

        # Determine source file
        if source_file is None:
            source_file = report.get("file_path")
            if not source_file:
                return {"redaction": {"status": "error", "error": "No source file provided"}}

        src_path = Path(source_file)
        if not src_path.exists():
            return {"redaction": {"status": "error", "error": f"Source file not found: {source_file}"}}

        suffix = src_path.suffix.lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        redaction_results: List[Dict] = []

        try:
            # ==================== PDF PROCESSING ====================
            if suffix == ".pdf":
                self.logger.info(f"Processing PDF: {src_path.name}")
                
                if not PDF2IMAGE_AVAILABLE or not OPENCV_AVAILABLE or not PIL_AVAILABLE:
                    return {"redaction": {"status": "error", 
                           "error": "Missing dependencies. Install: pip install pdf2image pillow opencv-python"}}
                
                # Poppler path for Windows
                POPPLER_PATH = None
                if os.name == 'nt':
                    POPPLER_PATH = r"C:\Users\Bhavana\Downloads\Release-25.07.0-0\poppler-25.07.0\Library\bin"
                
                # Convert PDF to images
                try:
                    pdf_pages = convert_from_path(str(src_path), dpi=400, poppler_path=POPPLER_PATH)
                    self.logger.info(f"Converted PDF to {len(pdf_pages)} page(s)")
                except Exception as e:
                    self.logger.error(f"PDF conversion failed: {e}")
                    return {"redaction": {"status": "error", "error": f"Failed to convert PDF: {e}"}}
                
                # Get PII locations
                pii_locations = report.get("pii_with_locations", {})
                method = self.config.get("default_image_method", "blur")
                
                if not pii_locations:
                    self.logger.warning("No PII locations found")
                    redacted_path = self.output_dirs["redacted"] / f"{src_path.stem}_redacted_{timestamp}.pdf"
                    pdf_pages[0].save(
                        str(redacted_path),
                        save_all=True,
                        append_images=pdf_pages[1:] if len(pdf_pages) > 1 else []
                    )
                    return {
                        "redaction": {
                            "status": "no_pii",
                            "output_path": str(redacted_path),
                            "entities_redacted": 0
                        }
                    }
                
                self.logger.info(f"Found {len(pii_locations)} PII items to redact")
                
                # Process each page
                redacted_pages = []
                for page_num, page_img in enumerate(pdf_pages):
                    # Convert PIL to OpenCV
                    img = cv2.cvtColor(np.array(page_img), cv2.COLOR_RGB2BGR)
                    img_shape = img.shape
                    
                    redacted_count = 0
                    
                    # Apply redactions with PRECISE bounding boxes
                    for pii_value, location in pii_locations.items():
                        bbox = self._calculate_precise_bbox(pii_value, location, img_shape)
                        
                        if not bbox:
                            self.logger.warning(f"Invalid bbox for: {pii_value[:40]}...")
                            continue
                        
                        x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']
                        
                        # Extract ROI
                        roi = img[y:y+h, x:x+w]
                        
                        if roi.size == 0:
                            self.logger.warning(f"Empty ROI for: {pii_value[:40]}...")
                            continue
                        
                        # Apply redaction method
                        redacted_roi = self._apply_redaction_to_roi(roi, method)
                        
                        # Replace in image
                        img[y:y+h, x:x+w] = redacted_roi
                        
                        redacted_count += 1
                        redaction_results.append({
                            "entity": {"value": pii_value, "page": page_num, "location": bbox},
                            "method": method,
                            "success": True
                        })
                        
                        self.logger.debug(f"Redacted: {pii_value[:30]}... at ({x}, {y}, {w}x{h})")
                    
                    self.logger.info(f"Page {page_num + 1}: Redacted {redacted_count} items")
                    
                    # Convert back to PIL
                    redacted_pages.append(Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)))
                
                # Save as PDF
                redacted_path = self.output_dirs["redacted"] / f"{src_path.stem}_redacted_{timestamp}.pdf"
                
                if redacted_pages:
                    redacted_pages[0].save(
                        str(redacted_path),
                        "PDF",
                        save_all=True,
                        append_images=redacted_pages[1:] if len(redacted_pages) > 1 else []
                    )
                    self.logger.info(f"Saved redacted PDF: {redacted_path}")

            # ==================== IMAGE PROCESSING ====================
            elif suffix in [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".gif"]:
                if not OPENCV_AVAILABLE:
                    return {"redaction": {"status": "error", "error": "OpenCV not installed"}}

                img = cv2.imread(str(src_path))
                if img is None:
                    return {"redaction": {"status": "error", "error": "Failed to load image"}}

                self.logger.info(f"Processing image: {src_path.name} ({img.shape})")
                img_shape = img.shape

                pii_locations = report.get("pii_with_locations", {})
                
                if not pii_locations:
                    redacted_path = self.output_dirs["redacted"] / f"{src_path.stem}_redacted_{timestamp}{suffix}"
                    cv2.imwrite(str(redacted_path), img)
                    return {
                        "redaction": {
                            "status": "no_pii",
                            "output_path": str(redacted_path),
                            "entities_redacted": 0
                        }
                    }

                method = self.config.get("default_image_method", "blur")
                
                for pii_value, location in pii_locations.items():
                    bbox = self._calculate_precise_bbox(pii_value, location, img_shape)
                    
                    if not bbox:
                        continue
                    
                    x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']
                    
                    roi = img[y:y+h, x:x+w]
                    if roi.size == 0:
                        continue
                    
                    redacted_roi = self._apply_redaction_to_roi(roi, method)
                    img[y:y+h, x:x+w] = redacted_roi
                    
                    redaction_results.append({
                        "entity": {"value": pii_value, "location": bbox},
                        "method": method,
                        "success": True
                    })

                redacted_path = self.output_dirs["redacted"] / f"{src_path.stem}_redacted_{timestamp}{suffix}"
                cv2.imwrite(str(redacted_path), img)

            # ==================== TEXT PROCESSING ====================
            elif suffix in [".txt", ".csv", ".md", ".json"]:
                text = src_path.read_text(encoding="utf-8", errors="ignore")
                entities = OctopiiAdapter.enrich_with_positions(report, text)

                sorted_entities = sorted(
                    [e for e in entities if e.start_pos is not None],
                    key=lambda x: x.start_pos,
                    reverse=True
                )

                for ent in sorted_entities:
                    try:
                        mask_char = self.config.get("mask_char", "█")
                        mask_len = max(1, ent.end_pos - ent.start_pos)
                        masked = mask_char * mask_len
                        text = text[:ent.start_pos] + masked + text[ent.end_pos:]
                        
                        redaction_results.append({
                            "entity": ent.to_dict(),
                            "method": "mask",
                            "success": True
                        })
                    except Exception as e:
                        self.logger.error(f"Failed to redact: {e}")

                redacted_path = self.output_dirs["redacted"] / f"{src_path.stem}_redacted_{timestamp}{suffix}"
                redacted_path.write_text(text, encoding="utf-8")

            else:
                from shutil import copy2
                redacted_path = self.output_dirs["redacted"] / f"{src_path.stem}_redacted_{timestamp}{suffix}"
                copy2(src_path, redacted_path)

            # Generate reports
            report_path = self.output_dirs["reports"] / f"{src_path.stem}_report_{timestamp}.json"
            audit_path = self.output_dirs["audit_logs"] / f"{src_path.stem}_audit_{timestamp}.json"

            full_report = {
                "source_file": str(src_path),
                "redacted_file": str(redacted_path),
                "file_type": suffix[1:],
                "timestamp": datetime.now().isoformat(),
                "detection_report": report,
                "redaction_results": redaction_results,
                "summary": {
                    "total_entities_detected": len(redaction_results),
                    "entities_redacted": sum(1 for r in redaction_results if r.get("success")),
                    "redaction_failures": sum(1 for r in redaction_results if not r.get("success")),
                    "confidence_threshold": self.config.get("confidence_threshold")
                }
            }

            report_path.write_text(json.dumps(full_report, indent=2), encoding="utf-8")
            audit_path.write_text(json.dumps({"audit": full_report}, indent=2), encoding="utf-8")

            return {
                "redaction": {
                    "status": "success",
                    "output_path": str(redacted_path),
                    "entities_redacted": full_report["summary"]["entities_redacted"]
                },
                "report": str(report_path)
            }

        except Exception as e:
            self.logger.exception("Redaction failed")
            return {"redaction": {"status": "error", "error": str(e)}}