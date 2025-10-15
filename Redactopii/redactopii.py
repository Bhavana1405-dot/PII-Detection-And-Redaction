#!/usr/bin/env python3
"""
Redactopii - PII Redaction Engine CLI
"""
import argparse
import json
import sys
from pathlib import Path

from core.redaction_engine import RedactionEngine
from core.config import RedactionConfig
from integrations.pipeline_integration import RedactionPipeline


def main():
    parser = argparse.ArgumentParser(description='PII Redaction Engine')
    parser.add_argument('--input', required=True, help='Input file path')
    parser.add_argument('--report', required=True, help='Octopii detection report')
    parser.add_argument('--output', help='Output directory')
    parser.add_argument('--config', help='Configuration file')
    
    args = parser.parse_args()
    
    # Initialize engine
    config = RedactionConfig(args.config) if args.config else RedactionConfig()
    engine = RedactionEngine(config)
    pipeline = RedactionPipeline(engine)
    
    # Process file
    result = pipeline.process_octopii_output(args.report, args.input)
    
    print(json.dumps(result, indent=2))
    
    return 0


if __name__ == '__main__':
    sys.exit(main())