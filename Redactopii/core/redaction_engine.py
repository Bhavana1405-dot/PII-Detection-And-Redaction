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
        self.logger = self._setup_logging()
        self.audit_log = []
        self.encryption_key = None
        
        # Create output directories
        self._setup_output_directories()
        
        if self.config.get("enable_encryption") and CRYPTO_AVAILABLE:
            self._initialize_encryption()
    
    def _setup_output_directories(self):
        """Create output directory structure"""
        base_dir = Path(self.config.get("output_base_dir", "./outputs"))
        
        self.output_dirs = {
            "redacted": base_dir / "redacted",
            "audit_logs": base_dir / "audit_logs",
            "reports": base_dir / "reports",
            "comparisons": base_dir / "comparisons"
        }
        
        for dir_path in self.output_dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"✓ Output directories created in: {base_dir}")
    
    def _setup_logging(self) -> logging.Logger:
        """Configure logging"""
        logger = logging.getLogger("RedactionEngine")
        logger.setLevel(getattr(logging, self.config.get("log_level", "INFO")))
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _initialize_encryption(self):
        """Initialize encryption key"""
        try:
            self.encryption_key = Fernet.generate_key()
            self.cipher = Fernet(self.encryption_key)
            self.logger.info("✓ Encryption initialized")
        except Exception as e:
            self.logger.error(f"Encryption init failed: {e}")
    
    def process_file(self, file_path: str, entities: List[PIIEntity]) -> Dict:
        """Process a file and redact detected PII"""
        self.logger.info(f"Processing file: {file_path}")
        
        if not entities:
            self.logger.warning("No PII entities to redact")
            return {
                "status": "no_pii",
                "message": "No PII entities detected"
            }
        
        file_ext = Path(file_path).suffix.lower()
        is_image = file_ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']
        
        if is_image and OPENCV_AVAILABLE:
            return self._process_image_file(file_path, entities)
        else:
            return self._process_text_file(file_path, entities)
    
    def _process_text_file(self, file_path: str, entities: List[PIIEntity]) -> Dict:
        """Process text file redaction"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            
            redacted_text, results = self._redact_text(text, entities, file_path)
            
            output_path = self._generate_output_path(file_path)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(redacted_text)
            
            self.logger.info(f"✓ Text file saved: {output_path}")
            
            if self.config.get("audit_trail"):
                self.audit_log.extend(results)
            
            return {
                "status": "success",
                "output_path": str(output_path),
                "entities_redacted": len([r for r in results if r.success]),
                "results": [r.to_dict() for r in results]
            }
        except Exception as e:
            self.logger.error(f"Text processing failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def _process_image_file(self, file_path: str, entities: List[PIIEntity]) -> Dict:
        """Process image file redaction"""
        try:
            img = cv2.imread(file_path)
            if img is None:
                raise ValueError(f"Cannot load image: {file_path}")
            
            original_img = img.copy()
            results = []
            
            # Filter entities with bounding boxes
            image_entities = [e for e in entities if e.bounding_box]
            
            if not image_entities:
                self.logger.warning("No bounding boxes for image redaction")
                return {
                    "status": "no_bounding_boxes",
                    "message": "Image has no bounding box data for redaction"
                }
            
            for entity in image_entities:
                if entity.confidence >= self.config.get("confidence_threshold", 0.7):
                    img = self._apply_image_redaction(img, entity)
                    results.append(RedactionResult(
                        original_entity=entity,
                        redacted_value="[REDACTED]",
                        method=RedactionMethod.BLUR,
                        timestamp=datetime.now().isoformat(),
                        file_path=file_path,
                        success=True
                    ))
            
            # Add watermark
            if self.config.get("add_watermark") and results:
                img = self._add_watermark(img)
            
            output_path = self._generate_output_path(file_path)
            cv2.imwrite(str(output_path), img)
            
            self.logger.info(f"✓ Image saved: {output_path}")
            
            # Save comparison
            if self.config.get("save_comparison") and results:
                self._save_comparison(original_img, img, file_path)
            
            if self.config.get("audit_trail"):
                self.audit_log.extend(results)
            
            return {
                "status": "success",
                "output_path": str(output_path),
                "entities_redacted": len(results),
                "results": [r.to_dict() for r in results]
            }
        except Exception as e:
            self.logger.error(f"Image processing failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def _redact_text(self, text: str, entities: List[PIIEntity], source_file: str) -> Tuple[str, List[RedactionResult]]:
        """Redact text content - handles entities with or without positions"""
        results = []
        redacted = text
        
        # Separate entities with and without positions
        positioned = [e for e in entities if e.start_pos is not None and e.end_pos is not None]
        unpositioned = [e for e in entities if e.start_pos is None or e.end_pos is None]
        
        # Redact positioned entities (most precise)
        sorted_positioned = sorted(positioned, key=lambda x: x.start_pos, reverse=True)
        
        for entity in sorted_positioned:
            if entity.confidence < self.config.get("confidence_threshold", 0.7):
                continue
            
            mask = self.config.get("mask_char", "█") * len(entity.value)
            redacted = redacted[:entity.start_pos] + mask + redacted[entity.end_pos:]
            
            results.append(RedactionResult(
                original_entity=entity,
                redacted_value=mask,
                method=RedactionMethod.MASK,
                timestamp=datetime.now().isoformat(),
                file_path=source_file,
                success=True
            ))
        
        # Redact unpositioned entities (find and replace all occurrences)
        for entity in unpositioned:
            if entity.confidence < self.config.get("confidence_threshold", 0.7):
                continue
            
            # Find all occurrences
            pattern = re.escape(entity.value)
            matches = list(re.finditer(pattern, redacted, re.IGNORECASE))
            
            if matches:
                mask = self.config.get("mask_char", "█") * len(entity.value)
                redacted = re.sub(pattern, mask, redacted, flags=re.IGNORECASE)
                
                results.append(RedactionResult(
                    original_entity=entity,
                    redacted_value=mask,
                    method=RedactionMethod.MASK,
                    timestamp=datetime.now().isoformat(),
                    file_path=source_file,
                    success=True
                ))
        
        return redacted, results
    
    def _apply_image_redaction(self, img, entity: PIIEntity):
        """Apply blur/blackbox/pixelate to image region"""
        bbox = entity.bounding_box
        padding = self.config.get("padding_pixels", 5)
        
        x = max(0, bbox.x - padding)
        y = max(0, bbox.y - padding)
        w = min(img.shape[1] - x, bbox.width + 2 * padding)
        h = min(img.shape[0] - y, bbox.height + 2 * padding)
        
        method = self.config.get("default_image_method", "blur")
        
        if method == "blur":
            roi = img[y:y+h, x:x+w]
            blurred = cv2.GaussianBlur(roi, (0, 0), self.config.get("blur_intensity", 25))
            img[y:y+h, x:x+w] = blurred
        elif method == "blackbox":
            cv2.rectangle(img, (x, y), (x+w, y+h), (0, 0, 0), -1)
        elif method == "pixelate":
            roi = img[y:y+h, x:x+w]
            block = self.config.get("pixelate_block_size", 15)
            small = cv2.resize(roi, (block, block))
            pixelated = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
            img[y:y+h, x:x+w] = pixelated
        
        return img
    
    def _add_watermark(self, img):
        """Add redaction watermark"""
        h, w = img.shape[:2]
        font = cv2.FONT_HERSHEY_SIMPLEX
        text = "REDACTED"
        cv2.putText(img, text, (w - 120, h - 10), font, 0.5, (0, 0, 255), 1)
        return img
    
    def _save_comparison(self, original, redacted, source_path):
        """Save side-by-side comparison"""
        try:
            comparison = np.hstack([original, redacted])
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(comparison, "ORIGINAL", (10, 30), font, 1, (255, 255, 255), 2)
            cv2.putText(comparison, "REDACTED", (original.shape[1] + 10, 30), font, 1, (255, 255, 255), 2)
            
            comparison_path = self.output_dirs["comparisons"] / f"{Path(source_path).stem}_comparison.png"
            cv2.imwrite(str(comparison_path), comparison)
            self.logger.info(f"✓ Comparison saved: {comparison_path}")
        except Exception as e:
            self.logger.error(f"Comparison save failed: {e}")
    
    def _generate_output_path(self, input_path: str) -> Path:
        """Generate output file path"""
        path = Path(input_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"{path.stem}_redacted_{timestamp}{path.suffix}"
        return self.output_dirs["redacted"] / output_name
    
    def process_octopii_report(self, report: Dict, source_file: str) -> Dict:
        """Process Octopii detection report"""
        from .integrations.octopii_adapter import OctopiiAdapter
        
        adapter = OctopiiAdapter()
        
        # Try enhanced parsing with source text
        try:
            with open(source_file, 'r', encoding='utf-8', errors='ignore') as f:
                source_text = f.read()
            entities = adapter.enrich_with_positions(report, source_text)
        except:
            entities = adapter.parse_report(report)
        
        result = self.process_file(source_file, entities)
        
        # Save comprehensive report
        report_path = self.output_dirs["reports"] / f"{Path(source_file).stem}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        full_report = {
            "source": source_file,
            "timestamp": datetime.now().isoformat(),
            "detection": report,
            "redaction": result
        }
        
        with open(report_path, 'w') as f:
            json.dump(full_report, f, indent=2)
        
        self.logger.info(f"✓ Report saved: {report_path}")
        
        # Save audit log
        if self.config.get("audit_trail") and self.audit_log:
            audit_path = self.output_dirs["audit_logs"] / f"{Path(source_file).stem}_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(audit_path, 'w') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "total_redactions": len(self.audit_log),
                    "redactions": [r.to_dict() for r in self.audit_log]
                }, f, indent=2)
            self.logger.info(f"✓ Audit log saved: {audit_path}")
        
        return full_report