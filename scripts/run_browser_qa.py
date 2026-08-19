#!/usr/bin/env python3
import json, sys
from app.browser_qa import run

url = sys.argv[1]
out = run(url, sys.argv[2] if len(sys.argv) > 2 else None)
print(json.dumps(out, indent=2))
sys.exit(0 if out.get('ok') or out.get('skipped') else 1)
