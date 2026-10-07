"""Build the committed evidence site using only Python's standard library."""
import json
import re
import shutil
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FILES={'index.html','experiments.html','site.css','site.js','_headers','report.json','report-v1.json','tutorial.md','experiment-results.md','experiment-results-v1.md','competitive.md','v02-validation.md','review-results.md','LICENSE.txt','product-prd.md','product-prd.zh-CN.md','v03-validation.md','workbench.html','workbench.css','workbench.js','workbench-evidence.json','v04-validation.md','workbench-prd.zh-CN.md','workbench-guide.en.md','trial-and-resume.zh-CN.md'}

def main():
    source=ROOT/'public-site';destination=ROOT/'dist'
    if {p.name for p in source.iterdir()}!=FILES:raise SystemExit('Unexpected source file in public-site')
    report=json.loads((source/'report.json').read_text(encoding='utf-8'))
    validate_upgrade(json.loads((source/'workbench-evidence.json').read_text(encoding='utf-8')))
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

def validate_upgrade(report):
    if set(report)!={'schema','mode','human_sessions','cases','limitations'} or report['schema']!='adoptlab-upgrade-evidence-v1' or report['mode']!='protocol' or report['human_sessions']!=0:raise ValueError('INVALID_UPGRADE_REPORT')
    if len(report['cases'])!=3:raise ValueError('THREE_CASES_REQUIRED')
    task_ids=set();run_ids=set()
    for case in report['cases']:
        if set(case)!={'task_id','runs','release'} or len(case['runs'])!=2:raise ValueError('INVALID_UPGRADE_CASE')
        if not isinstance(case['task_id'],str) or case['task_id'] in task_ids:raise ValueError('DUPLICATE_UPGRADE_TASK')
        task_ids.add(case['task_id'])
        for run in case['runs']:
            if set(run)!={'id','status','passed','condition','task_hash','material_hash','artifact_hash','mode','cohort'} or run['mode']!='protocol' or run['cohort']!='automation' or type(run['passed']) is not bool:raise ValueError('INVALID_UPGRADE_RUN')
            if not isinstance(run['id'],str) or not re.fullmatch('[a-f0-9]{32}',run['id']) or run['id'] in run_ids:raise ValueError('DUPLICATE_OR_INVALID_UPGRADE_RUN')
            run_ids.add(run['id'])
            if run['status'] not in {'succeeded','failed','cancelled','uncertain','budget_exhausted','timed_out','interrupted'} or run['passed'] and run['status']!='succeeded':raise ValueError('INVALID_UPGRADE_STATUS')
            if any(not re.fullmatch('[a-f0-9]{64}',run[k]) for k in ['condition','task_hash','material_hash','artifact_hash']):raise ValueError('INVALID_UPGRADE_FINGERPRINT')
        if set(case['release'])!={'verdict','comparable'} or case['release']['verdict'] not in ['passed','failed','insufficient'] or type(case['release']['comparable']) is not bool:raise ValueError('INVALID_UPGRADE_GATE')
        before,after=case['runs']
        comparable=all(before[k]==after[k] for k in ['condition','task_hash'])
        if case['release']['comparable']!=comparable:raise ValueError('UPGRADE_COMPARABILITY_MISMATCH')
        if case['release']['verdict']=='passed' and (not comparable or not after['passed'] or before['material_hash']==after['material_hash']):raise ValueError('UNSUPPORTED_UPGRADE_RELEASE')

if __name__=='__main__':main()
