from pathlib import Path
import sys
sys.path.insert(0, str(Path('Redactopii')))
from Redactopii.core.redaction_engine import RedactionEngine
from Redactopii.core.config import RedactionConfig

c = RedactionConfig()
engine = RedactionEngine(c)
print('Engine initialized OK')
print('Output dirs:')
for k, v in engine.output_dirs.items():
    print(' -', k, v)
