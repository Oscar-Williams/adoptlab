"""Build the committed evidence site using only Python's standard library."""
import json
import re
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FILES={'index.html','site.css','site.js','_headers','report.json','tutorial.md','experiment-results.md','competitive.md','LICENSE.txt'}

def main():
    source=ROOT/'public-site';destination=ROOT/'dist'
    if {p.name for p in source.iterdir()}!=FILES:raise SystemExit('Unexpected source file in public-site')
    report=json.loads((source/'report.json').read_text(encoding='utf-8'))
    assert report['schema']=='adoptlab-static-evidence-v1' and len(report['cases'])==72
    assert sum(x['passed'] for x in report['cases'] if x['material']=='A')==21
    assert sum(x['passed'] for x in report['cases'] if x['material']=='B')==36
    pattern=re.compile(rb'sk-(?:lf-)?[A-Za-z0-9_-]{20,}|pk-lf-[A-Za-z0-9_-]{20,}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----|[A-Z]:[\\/](?:Users|Agent_Related)[\\/]')
    for name in FILES:
        if pattern.search((source/name).read_bytes()):raise SystemExit('Private content rejected: '+name)
    destination.mkdir(exist_ok=True)
    if {p.name for p in destination.iterdir()}-FILES:raise SystemExit('Unexpected existing dist files; inspect before deployment')
    for name in FILES:shutil.copy2(source/name,destination/name)
    print(json.dumps({'files':len(FILES),'episodes':72,'backend_included':False,'credentials_required':False,'output':'dist'}))

if __name__=='__main__':main()
