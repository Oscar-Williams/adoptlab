"""Competitor launch boundary: remove inherited credentials before serving MCP."""
import json
import os
import sys
from pathlib import Path

def main():
    root=Path(sys.argv[1]).resolve();material=sys.argv[2]
    if not (root/'fixtures'/'records.json').is_file():raise SystemExit('Prepared synthetic fixture required')
    keep={'PATH','SYSTEMROOT','COMSPEC','TEMP','TMP','PATHEXT','PYTHONPATH','PYTHONIOENCODING'}
    retained={k:v for k,v in os.environ.items() if k.upper() in keep}
    os.environ.clear();os.environ.update(retained)
    from adoptlab.server import build
    build(root,material).run(transport='stdio')

if __name__=='__main__':main()
