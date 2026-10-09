from pathlib import Path
import sys

from app.scanner import DataScanner

root = Path(__file__).resolve().parents[1]
scanner = DataScanner(root / "data", cache_seconds=0)
result = scanner.get(force=True)
errors = scanner.validate_references(result)
for item in errors:
    print(f"ERROR {item['path']}: {item['message']}")
print(f"Scanned {len(result.records)} valid article(s).")
sys.exit(1 if errors else 0)
