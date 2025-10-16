#!/usr/bin/env python3
"""
Redactopii - PII Redaction Engine CLI
"""
import argparse
import json
import sys
from pathlib import Path

# We add necessary imports for image processing and data models
import cv2
from core.models import PIIEntity, PIIType, BoundingBox
from utils.file_handler import FileHandler

def parse_report(report: dict) -> list[PIIEntity]:
    """
    Parses the Octopii JSON report into a list of PIIEntity objects.
    This logic is borrowed from the OctopiiAdapter.
    """
    entities = []
    detected_items = report.get("pii_detected", [])
    
    for item in detected_items:
        entity_type_str = item.get("type", "custom").lower()
        try:
            entity_type = PIIType(entity_type_str)
        except ValueError:
            entity_type = PIIType.CUSTOM
            
        bbox_data = item.get("bounding_box")
        bbox = None
        if bbox_data:
            bbox = BoundingBox(
                x=bbox_data.get("x", 0),
                y=bbox_data.get("y", 0),
                width=bbox_data.get("width", 0),
                height=bbox_data.get("height", 0),
                page=bbox_data.get("page", 0) # Page is ignored for single images
            )
        
        if bbox: # Only process entities that have a bounding box for image redaction
            entity = PIIEntity(
                entity_type=entity_type,
                value=item.get("value", ""),
                confidence=item.get("confidence", 1.0),
                bounding_box=bbox,
            )
            entities.append(entity)
            
    return entities


def redact_image_file(image_path: str, entities: list[PIIEntity], output_dir: str):
    """
    Loads an image, draws black boxes over PII, and saves the redacted image.
    """
    print(f"Loading image from: {image_path}")
    image = cv2.imread(image_path)
    
    if image is None:
        print(f"Error: Could not load image at {image_path}", file=sys.stderr)
        return None

    redactions_performed = 0
    for entity in entities:
        if entity.bounding_box:
            bb = entity.bounding_box
            # Define the top-left (start) and bottom-right (end) points of the rectangle
            start_point = (bb.x, bb.y)
            end_point = (bb.x + bb.width, bb.y + bb.height)
            # Draw a filled black rectangle over the PII
            cv2.rectangle(image, start_point, end_point, color=(0, 0, 0), thickness=-1)
            redactions_performed += 1
            
    print(f"Performed {redactions_performed} redactions on the image.")

    # Generate a new filename and save the redacted image
    output_filename = FileHandler.generate_output_path(Path(image_path).name)
    output_path = Path(output_dir) / output_filename
    
    # Ensure the output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    cv2.imwrite(str(output_path), image)
    print(f"✓ Redacted file saved successfully to: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description='PII Redaction Engine')
    parser.add_argument('--input', required=True, help='Input image file path')
    parser.add_argument('--report', required=True, help='Octopii detection report (JSON)')
    parser.add_argument('--output', required=True, help='Output directory to save redacted file')
    
    args = parser.parse_args()
    
    # Load the detection report
    try:
        with open(args.report, 'r') as f:
            report_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Report file not found at {args.report}", file=sys.stderr)
        return 1
    
    # Parse the report to get PII entities
    pii_entities = parse_report(report_data)
    
    if not pii_entities:
        print("No PII with bounding boxes found in the report. Nothing to redact.")
        return 0

    # Perform the redaction and save the file
    redact_image_file(args.input, pii_entities, args.output)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())