#!/usr/bin/env python3
"""
Performance benchmarking for redaction operations
"""
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from Redactopii.core.redaction_engine import RedactionEngine
from Redactopii.core.config import RedactionConfig
from Redactopii.core.models import PIIEntity, PIIType
from Redactopii.redactors.text_redactor import TextRedactor


def benchmark_text_redaction(num_entities: int = 100):
    """Benchmark text redaction performance"""
    
    print(f"\nBenchmarking text redaction with {num_entities} entities...")
    
    config = RedactionConfig()
    redactor = TextRedactor(config)
    
    # Generate test data
    text = "Email: test@example.com " * num_entities
    entities = []
    
    for i in range(num_entities):
        offset = i * 25
        entities.append(PIIEntity(
            entity_type=PIIType.EMAIL,
            value="test@example.com",
            confidence=0.9,
            start_pos=7 + offset,
            end_pos=23 + offset
        ))
    
    # Benchmark
    start = time.time()
    redacted_text, results = redactor.redact(text, entities)
    end = time.time()
    
    duration = end - start
    throughput = num_entities / duration
    
    print(f"  Duration: {duration:.4f} seconds")
    print(f"  Throughput: {throughput:.2f} entities/second")
    print(f"  Success rate: {len([r for r in results if r.success])}/{num_entities}")


def main():
    print("=" * 60)
    print("Redactopii Performance Benchmark")
    print("=" * 60)
    
    benchmark_text_redaction(100)
    benchmark_text_redaction(1000)
    benchmark_text_redaction(10000)
    
    print("\n" + "=" * 60)
    print("Benchmark complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()