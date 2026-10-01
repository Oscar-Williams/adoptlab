"""Build the committed evidence site using only Python's standard library."""
import json
import re
import shutil
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FILES={'index.html','site.css','site.js','_headers','report.json','report-v1.json','tutorial.md','experiment-results.md','experiment-results-v1.md','competitive.md','v02-validation.md','review-results.md','LICENSE.txt'}

def main():
    source=ROOT/'public-site';destination=ROOT/'dist'
    if {p.name for p in source.iterdir()}!=FILES:raise SystemExit('Unexpected source file in public-site')
    report=json.loads((source/'report.json').read_text(encoding='utf-8'))
    validate_report(report)
    validate_report(json.loads((source/'report-v1.json').read_text(encoding='utf-8')))
    pattern=re.compile(rb'sk-(?:lf-)?[A-Za-z0-9_-]{20,}|pk-lf-[A-Za-z0-9_-]{20,}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----|[A-Z]:[\\/](?:Users|Agent_Related)[\\/]')
    for name in FILES:
        if pattern.search((source/name).read_bytes()):raise SystemExit('Private content rejected: '+name)
    destination.mkdir(exist_ok=True)
    if {p.name for p in destination.iterdir()}-FILES:raise SystemExit('Unexpected existing dist files; inspect before deployment')
    for name in FILES:shutil.copy2(source/name,destination/name)
    print(json.dumps({'files':len(FILES),'episodes':len(report['cases']),'backend_included':False,'credentials_required':False,'output':'dist'}))

def validate_report(report):
    if report.get('schema') not in {'adoptlab-static-evidence-v1','adoptlab-static-evidence-v2'}:raise ValueError('UNKNOWN_REPORT_SCHEMA')
    if set(report)-{'schema','recorded_date','model','materials','cases','limitations'}:raise ValueError('UNEXPECTED_PUBLIC_FIELD')
    if not isinstance(report.get('cases'),list) or not report['cases']:raise ValueError('EMPTY_REPORT')
    allowed={'task_id','family','split','material','trial','passed','kind','reason','cost_upper_cny','elapsed_seconds','error_code','requests','tools','mode','cohort','status','condition','responder'}
    for row in report['cases']:
        if set(row)-allowed or type(row.get('passed')) is not bool or type(row.get('cost_upper_cny')) not in (int,float) or not math.isfinite(row['cost_upper_cny']) or row['cost_upper_cny']<0:raise ValueError('INVALID_PUBLIC_CASE')
        if not all(isinstance(row.get(k),str) for k in ['task_id','family','kind','reason']) or type(row.get('trial')) is not int or row['trial']<1:raise ValueError('INVALID_PUBLIC_CASE')
        if report['schema'].endswith('v2') and (row.get('mode') not in {'protocol','model'} or row.get('status') not in {'succeeded','failed','cancelled','uncertain','budget_exhausted','timed_out','interrupted'} or not re.fullmatch('[a-f0-9]{64}',row.get('condition',''))):raise ValueError('INVALID_PUBLIC_CONDITION')
        if row.get('material') not in report['materials']:raise ValueError('UNKNOWN_MATERIAL')
    for material in report['materials'].values():
        if set(material)!={'guide','descriptions'}:raise ValueError('INVALID_PUBLIC_MATERIAL')

if __name__=='__main__':main()
