# =============================================================================
# FILE: Redactopii/core/redaction_engine.py
# DESCRIPTION: Core redaction engine with automatic file output
# =============================================================================

"""
Core redaction engine - orchestrates all redaction operations
Automatically saves redacted files to outputs/ directory
"""
import logging
import json
import hashlib
import re
from typing import Dict, List, Optional, Tuple
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
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


class RedactionEngine:
    """Main orchestrator for redaction operations with automatic file output"""
    
    def __init__(self, config: Optional[RedactionConfig] = None):
        self.config = config or RedactionConfig()
        # Logger
        self.logger = self._setup_logging()

        # Audit trail and optional encryption key
        self.audit_log: List[Dict] = []
        self.encryption_key: Optional[bytes] = None

        # Prepare output directories
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
        """Create a simple logger for the engine using config log_level."""
        level = self.config.get("log_level", "INFO")
        logger = logging.getLogger("RedactionEngine")
        if not logger.handlers:
            handler = logging.StreamHandler()
            fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                     datefmt='%Y-%m-%d %H:%M:%S')
            handler.setFormatter(fmt)
            logger.addHandler(handler)
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        return logger

    def process_octopii_report(self, report: Dict, source_file: Optional[str] = None) -> Dict:
        """Basic processing of an Octopii report. Returns a result dict used by the pipeline.

        This is a minimal, safe implementation: for text files it masks detected values;
        for non-text files it copies the source to the redacted directory (no-op).
        """
        from integrations.octopii_adapter import OctopiiAdapter

        # Determine source file
        if source_file is None:
            source_file = report.get("file_path")
            if not source_file:
                raise ValueError("No source file provided or found in report")

        src_path = Path(source_file)
        if not src_path.exists():
            return {"redaction": {"status": "error", "error": f"Source file not found: {source_file}"}}

        suffix = src_path.suffix.lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        redacted_path = self.output_dirs["redacted"] / f"{src_path.stem}_redacted_{timestamp}{suffix}"

        redaction_results: List[Dict] = []

        # Handle text-like files
        if suffix in [".txt", ".csv", ".md", ".json"]:
            text = src_path.read_text(encoding="utf-8", errors="ignore")

            entities = OctopiiAdapter.enrich_with_positions(report, text)

            for ent in entities:
                try:
                    start = ent.start_pos
                    end = ent.end_pos
                    if start is not None and end is not None:
                        mask_char = self.config.get("mask_char", "█")
                        masked = mask_char * max(1, end - start)
                        text = text[:start] + masked + text[end:]
                        redaction_results.append({"entity": ent.to_dict(), "method": "mask", "success": True})
                    else:
                        # fallback: replace value occurrences
                        if ent.value:
                            mask_char = self.config.get("mask_char", "█")
                            text = text.replace(ent.value, mask_char * max(1, len(ent.value)))
                            redaction_results.append({"entity": ent.to_dict(), "method": "mask", "success": True})
                except Exception as e:
                    self.logger.exception("Failed to redact entity")
                    redaction_results.append({"entity": ent.to_dict(), "method": "mask", "success": False, "error": str(e)})

            redacted_path.write_text(text, encoding="utf-8")

        else:
            # Non-text: copy as-is (no-op redaction) - minimal safe behaviour
            try:
                from shutil import copy2
                copy2(src_path, redacted_path)
            except Exception as e:
                return {"redaction": {"status": "error", "error": str(e)}}

        # Write report and audit
        report_path = self.output_dirs["reports"] / f"{src_path.stem}_report_{timestamp}.json"
        audit_path = self.output_dirs["audit_logs"] / f"{src_path.stem}_audit_{timestamp}.json"

        full_report = {
            "source_file": str(src_path),
            "redacted_file": str(redacted_path),
            "file_type": "text" if suffix in [".txt", ".csv", ".md", ".json"] else "binary",
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

        try:
            report_path.write_text(json.dumps(full_report, indent=2), encoding="utf-8")
            audit_path.write_text(json.dumps({"audit": full_report}, indent=2), encoding="utf-8")
        except Exception:
            self.logger.exception("Failed to write report/audit files")

        return {"redaction": {"status": "success", "output_path": str(redacted_path), "entities_redacted": full_report["summary"]["entities_redacted"]}, "report": str(report_path)}