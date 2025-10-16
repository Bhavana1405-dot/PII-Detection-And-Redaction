# Complete Usage Guide: Octopii Detection → Redaction

## Overview

This guide shows you how to use your existing Octopii scanner with the new Redaction Engine to automatically detect and redact PII from files.

---

## 🚀 Quick Start

### 1. Setup Environment

```bash
# From your PII_REDACTION directory
bash setup_redaction_engine.sh

# Activate environment
source venv/bin/activate

# Install dependencies
pip install -r Redactopii/requirements.txt
```

### 2. Run Octopii Detection (Your Existing Code)

```bash
cd Octopii
python octopii.py /path/to/your/file.txt
```

**Output:** `output.json` containing detected PII

Example `output.json`:
```json
{
    "file_path": "customer_data.txt",
    "pii_class": "financial",
    "score": 67,
    "country_of_origin": "US",
    "faces": 0,
    "identifiers": ["123-45-6789", "4532015112830366"],
    "emails": ["john.doe@example.com"],
    "phone_numbers": ["+1-555-123-4567"],
    "addresses": ["123 Main St, Springfield, IL"]
}
```

### 3. Run Redaction

```bash
cd ..
python Redactopii/redactopii.py \
  --input customer_data.txt \
  --report Octopii/output.json
```

**Output Files Created:**
```
outputs/
├── redacted/
│   └── customer_data_redacted_20250116_143022.txt  ← Masked file
├── reports/
│   └── customer_data_report_20250116_143022.json   ← Full report
└── audit_logs/
    └── customer_data_audit_20250116_143022.json    ← Audit trail
```

---

## 📋 Step-by-Step Workflow

### Step 1: Detect PII with Octopii

```bash
# Scan a single file
python Octopii/octopii.py document.txt

# Scan a directory
python Octopii/octopii.py /path/to/documents/

# Scan an image
python Octopii/octopii.py scan.png

# Scan a PDF
python Octopii/octopii.py report.pdf
```

### Step 2: Review Detection Results

```bash
# View the output
cat Octopii/output.json
```

Look for:
- ✅ `emails`: Email addresses found
- ✅ `phone_numbers`: Phone numbers found
- ✅ `identifiers`: SSN, credit cards, IDs
- ✅ `addresses`: Physical addresses
- ✅ `faces`: Face detection count

### Step 3: Redact the File

**Option A: Simple Redaction**
```bash
python Redactopii/redactopii.py \
  --input document.txt \
  --report Octopii/output.json
```

**Option B: Custom Redaction Method**
```bash
# For images - use pixelate
python Redactopii/redactopii.py \
  --input scan.png \
  --report Octopii/output.json \
  --method pixelate

# For images - use blur (default)
python Redactopii/redactopii.py \
  --input scan.png \
  --report Octopii/output.json \
  --method blur

# For images - use blackbox
python Redactopii/redactopii.py \
  --input scan.png \
  --report Octopii/output.json \
  --method blackbox
```

**Option C: Custom Output Directory**
```bash
python Redactopii/redactopii.py \
  --input document.txt \
  --report Octopii/output.json \
  --output-dir ./my_redacted_files
```

### Step 4: Review Redacted Files

```bash
# View redacted text file
cat outputs/redacted/document_redacted_*.txt

# Open redacted image
xdg-open outputs/redacted/scan_redacted_*.png

# View comparison (for images)
xdg-open outputs/comparisons/scan_comparison_*.png

# Review audit log
cat outputs/audit_logs/document_audit_*.json
```

---

## 🔧 Advanced Usage

### A. Batch Processing Multiple Files

If Octopii scanned multiple files:

**1. Octopii output with multiple files:**
```json
[
  {
    "file_path": "file1.txt",
    "emails": ["user1@example.com"],
    ...
  },
  {
    "file_path": "file2.txt",
    "emails": ["user2@example.com"],
    ...
  }
]
```

**2. Batch redact all files:**
```python
# Create a batch script: batch_redact.py
from Redactopii.integrations.pipeline_integration import batch_redact_from_octopii

results = batch_redact_from_octopii(
    octopii_output_file="Octopii/output.json",
    output_dir="./outputs"
)

print(f"Processed: {results['total_files']}")
print(f"Success: {results['successful']}")
print(f"Failed: {results['failed']}")
```

```bash
python batch_redact.py
```

### B. Python API Usage

```python
from Redactopii.core.redaction_engine import RedactionEngine
from Redactopii.core.config import RedactionConfig
from Redactopii.integrations.pipeline_integration import RedactionPipeline

# Initialize with custom config
config = RedactionConfig()
config.set("confidence_threshold", 0.80)  # Higher threshold
config.set("default_image_method", "pixelate")
config.set("save_comparison", True)

# Create engine and pipeline
engine = RedactionEngine(config)
pipeline = RedactionPipeline(engine)

# Process single file
result = pipeline.process_octopii_output(
    report_path="Octopii/output.json",
    source_file="document.txt"
)

# Check result
if result["redaction"]["status"] == "success":
    print(f"✓ Redacted: {result['redaction']['output_path']}")
else:
    print(f"✗ Failed: {result['redaction']['error']}")
```

### C. Custom Configuration File

**1. Create config file: `my_config.json`**
```json
{
  "default_text_method": "mask",
  "default_image_method": "blur",
  "mask_char": "█",
  "blur_intensity": 30,
  "pixelate_block_size": 20,
  "confidence_threshold": 0.75,
  "save_comparison": true,
  "add_watermark": true,
  "output_base_dir": "./my_outputs"
}
```

**2. Use custom config:**
```bash
python Redactopii/redactopii.py \
  --input document.txt \
  --report Octopii/output.json \
  --config my_config.json
```

---

## 📊 Understanding the Output

### Redacted Text File

**Original:**
```
Customer: John Doe
Email: john.doe@example.com
Phone: 555-123-4567
SSN: 123-45-6789
```

**Redacted:**
```
Customer: John Doe
Email: ███████████████████████
Phone: ████████████
SSN: ███████████
```

### Redacted Image File

- **Blur Method**: PII areas are Gaussian blurred
- **Blackbox Method**: PII areas covered with black rectangles
- **Pixelate Method**: PII areas pixelated (mosaic effect)
- **Watermark**: "REDACTED" stamp in corner (if enabled)

### Report JSON Structure

```json
{
  "source_file": "document.txt",
  "redacted_file": "outputs/redacted/document_redacted_20250116_143022.txt",
  "file_type": "text",
  "timestamp": "2025-01-16T14:30:22.123456",
  "detection_report": {
    "file_path": "document.txt",
    "pii_class": "financial",
    "score": 67,
    "emails": ["john.doe@example.com"],
    "phone_numbers": ["555-123-4567"],
    "identifiers": ["123-45-6789"]
  },
  "redaction_results": [
    {
      "original_entity": {
        "entity_type": "email",
        "value": "john.doe@example.com",
        "confidence": 0.95
      },
      "redacted_value": "███████████████████████",
      "method": "mask",
      "success": true
    }
  ],
  "summary": {
    "total_entities_detected": 3,
    "entities_redacted": 3,
    "redaction_failures": 0,
    "confidence_threshold": 0.7
  }
}
```

---

## 🎯 Common Use Cases

### Use Case 1: Redact Customer Data

```bash
# 1. Scan customer database export
python Octopii/octopii.py customer_export.csv

# 2. Redact sensitive fields
python Redactopii/redactopii.py \
  --input customer_export.csv \
  --report Octopii/output.json

# 3. Share redacted version
cp outputs/redacted/customer_export_redacted_*.csv ./safe_to_share/
```

### Use Case 2: Redact Scanned Documents

```bash
# 1. Scan document image
python Octopii/octopii.py scanned_contract.png

# 2. Redact with blur
python Redactopii/redactopii.py \
  --input scanned_contract.png \
  --report Octopii/output.json \
  --method blur

# 3. Review comparison
xdg-open outputs/comparisons/scanned_contract_comparison_*.png
```

### Use Case 3: Bulk Redaction of Documents

```bash
# 1. Scan entire directory
python Octopii/octopii.py /path/to/documents/

# 2. Create batch script
cat > batch_redact.py << 'EOF'
import json
from pathlib import Path
from Redactopii.integrations.pipeline_integration import quick_redact

# Load Octopii results
with open('Octopii/output.json', 'r') as f:
    reports = json.load(f)

# Handle both single and multiple reports
if isinstance(reports, dict):
    reports = [reports]

# Process each file
for report in reports:
    source_file = report['file_path']
    try:
        output = quick_redact(
            octopii_json='Octopii/output.json',
            source_file=source_file,
            output_dir='./bulk_outputs'
        )
        print(f"✓ {source_file} → {output}")
    except Exception as e:
        print(f"✗ {source_file}: {e}")
EOF

# 3. Run batch redaction
python batch_redact.py
```

---

## 🔍 Troubleshooting

### Issue 1: "No PII entities detected"

**Cause:** Octopii didn't find any PII, or output.json is empty

**Solution:**
```bash
# Check Octopii output
cat Octopii/output.json

# Verify file has PII
cat your_file.txt

# Try with lower confidence threshold
python Redactopii/redactopii.py \
  --input file.txt \
  --report Octopii/output.json \
  --config low_threshold_config.json
```

### Issue 2: "Source file not found"

**Cause:** File path in output.json doesn't match actual file location

**Solution:**
```bash
# Override source file path
python Redactopii/redactopii.py \
  --input /correct/path/to/file.txt \
  --report Octopii/output.json
```

### Issue 3: Image redaction not working

**Cause:** Missing OpenCV or PIL dependencies

**Solution:**
```bash
pip install opencv-python pillow numpy
```

### Issue 4: Text positions not found

**Cause:** Octopii doesn't provide position data by default

**Effect:** All occurrences of PII are redacted (less precise)

**Solution:** This is expected behavior. The adapter finds and redacts all occurrences.

---

## 📁 File Structure After Processing

```
PII_REDACTION/
├── Octopii/
│   ├── octopii.py
│   └── output.json                          ← Detection results
├── Redactopii/
│   ├── redactopii.py                        ← CLI tool
│   └── ...
├── outputs/                                  ← All outputs here
│   ├── redacted/                            ← REDACTED FILES
│   │   ├── file1_redacted_20250116_143022.txt
│   │   └── scan_redacted_20250116_143022.png
│   ├── comparisons/                         ← Before/after images
│   │   └── scan_comparison_20250116_143022.png
│   ├── audit_logs/                          ← Audit trails
│   │   └── file1_audit_20250116_143022.json
│   └── reports/                             ← Full reports
│       └── file1_report_20250116_143022.json
└── your_source_files/
    ├── file1.txt
    └── scan.png
```

---

## 🎨 Redaction Method Comparison

| Method | Best For | Pros | Cons |
|--------|----------|------|------|
| **BLUR** | Images, Photos | Natural look, readable context | May be reversible with advanced tools |
| **BLACKBOX** | Documents, Forms | Complete coverage, irreversible | Obvious redaction |
| **PIXELATE** | Screenshots, UI | Modern look, clear intent | Slightly reversible |
| **MASK** | Text files | Fast, simple | Only for text |

---

## 🔐 Security Best Practices

1. **Always review redacted files** before sharing
2. **Keep audit logs** for compliance tracking
3. **Use blackbox for critical data** (SSN, credit cards)
4. **Store encryption keys securely** if using reversible redaction
5. **Delete temp files** after processing
6. **Test on sample data** before production use

---

## 📞 Support & Resources

### Quick Reference Commands

```bash
# Basic redaction
python Redactopii/redactopii.py --input FILE --report output.json

# With method
python Redactopii/redactopii.py --input FILE --report output.json --method blur

# Custom output
python Redactopii/redactopii.py --input FILE --report output.json --output-dir ./my_output

# Help
python Redactopii/redactopii.py --help
```

### Configuration Reference

| Setting | Default | Options |
|---------|---------|---------|
| `default_text_method` | `mask` | `mask`, `hash`, `encrypt`, `blackbox` |
| `default_image_method` | `blur` | `blur`, `blackbox`, `pixelate` |
| `confidence_threshold` | `0.7` | `0.0` to `1.0` |
| `blur_intensity` | `25` | `1` to `100` |
| `pixelate_block_size` | `15` | `5` to `50` |
| `save_comparison` | `true` | `true`, `false` |
| `add_watermark` | `true` | `true`, `false` |

---

## ✅ Verification Checklist

Before deploying to production:

- [ ] Run Octopii on sample files
- [ ] Verify output.json contains detected PII
- [ ] Run redaction on test files
- [ ] Check redacted files are properly masked
- [ ] Review audit logs are complete
- [ ] Test batch processing
- [ ] Verify output directory permissions
- [ ] Document your workflow
- [ ] Train team on usage
- [ ] Set up backup procedures

---

## 🚀 Next Steps

1. **Test with your real data:**
   ```bash
   python Octopii/octopii.py your_sensitive_file.txt
   python Redactopii/redactopii.py --input your_sensitive_file.txt --report Octopii/output.json
   ```

2. **Create your workflow script:**
   - Automate detection + redaction
   - Add to CI/CD pipeline
   - Schedule regular scans

3. **Customize for your needs:**
   - Adjust confidence thresholds
   - Choose redaction methods
   - Configure output locations

4. **Monitor and maintain:**
   - Review audit logs regularly
   - Update PII patterns in Octopii
   - Test new file types

---

**Ready to start? Run the setup script and follow Step 1! 🎉**