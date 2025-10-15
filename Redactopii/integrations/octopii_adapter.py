"""
Adapter for parsing Octopii detection reports
"""
import json
from typing import List
from ..core.models import PIIEntity, BoundingBox

class OctopiiAdapter:
    """Converts Octopii detection reports into standard PIIEntity objects"""
    
    @staticmethod
    def parse_report(report_path: str) -> List[PIIEntity]:
        with open(report_path, 'r', encoding='utf-8') as file:
            report_data = json.load(file)
        
        entities = []
        for item in report_data.get("detections", []):
            entity = PIIEntity(
                entity_type=item.get("type"),
                value=item.get("value"),
                start_pos=item.get("start_pos"),
                end_pos=item.get("end_pos"),
                confidence=item.get("confidence", 1.0),
                bounding_box=BoundingBox(**item.get("bounding_box", {})) if item.get("bounding_box") else None
            )
            entities.append(entity)
        
        return entities
