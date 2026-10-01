"""Create an allowlisted static publication bundle, without backend or credentials."""
import json
import re
import shutil
import argparse
from pathlib import Path
from dotenv import dotenv_values
from adoptlab.config import CODE,RUNTIME
from adoptlab.store import Store
from adoptlab.tasks import MATERIALS,catalog

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--experiment');parser.add_argument('--protocol',type=Path);args=parser.parse_args()
    output=RUNTIME.parent/'publication'/'adoptlab-site';output.mkdir(parents=True,exist_ok=True)
    source=CODE/'public-site'
    for name in ['index.html','site.css','site.js','_headers']:shutil.copy2(source/name,output/name)
    for name in ['tutorial.md','experiment-results.md','competitive.md','v02-validation.md','review-results.md']:shutil.copy2(CODE/'docs'/name,output/name)
    for name in ['report-v1.json','experiment-results-v1.md']:shutil.copy2(source/name,output/name)
    shutil.copy2(CODE/'LICENSE',output/'LICENSE.txt')
    tutorial=output/'tutorial.md'
    tutorial.write_text(tutorial.read_text(encoding='utf-8').replace('(mcp-task-packages.md)','(https://github.com/Oscar-Williams/adoptlab/blob/main/docs/mcp-task-packages.md)'),encoding='utf-8')
    s=Store();e=s.get_experiment(args.experiment) if args.experiment else next(e for e in s.experiments() if e['title']=='Frozen exploratory matrix v1')
    cases=[]
    for r in s.runs(e['id']):
        if r['status'] in {'queued','running'} or not r['result']:raise ValueError('EXPERIMENT_NOT_TERMINAL')
        v=r['result']['verification'];cases.append({'task_id':r['task_id'],'family':s.task(r['task_id'])['family'],
            'material':r['material'],'trial':r['trial'],'passed':r['status']=='succeeded' and v['passed'],
            'kind':v.get('kind','execution_error'),'reason':v.get('reason','execution_error'),'cost_upper_cny':r['result'].get('cost_upper_cny',0)})
    report={'schema':'adoptlab-static-evidence-v1','recorded_date':'2026-09-30','model':'deepseek-flash','materials':MATERIALS,'cases':cases,
            'limitations':'One model, synthetic records, correlated repeats and bundled guide/description changes. This is a recorded explorer, with no live inference or unique-user claim.'}
    if args.experiment:
        report.update(schema='adoptlab-static-evidence-v2',recorded_date=e['created'][:10],model=e['config']['model'],materials={id:s.material(id)['content'] for id in dict.fromkeys(r['material'] for r in s.runs(e['id']))},limitations='Saved terminal runs with independent task acceptance; synthetic tasks and correlated repeats. Compare execution conditions before interpreting material effects. No live inference or observed human-adoption claim.')
        aliases={}
        if args.protocol:
            protocol=json.loads(args.protocol.read_text(encoding='utf-8'))
            if protocol['experiment_id']!=e['id']:raise ValueError('PROTOCOL_EXPERIMENT_MISMATCH')
            aliases={v:k for k,v in protocol['variants'].items()}
            report['materials']={aliases.get(k,k):v for k,v in report['materials'].items()}
        for case,run in zip(cases,s.runs(e['id'])):
            case.update(material=aliases.get(case['material'],case['material']),mode=run['mode'],cohort=run['cohort'],status=run['status'],split=s.task(run['task_id'])['split'],condition=s.condition(run),responder=run['result'].get('provenance',{}).get('model'))
    from build_static_site import validate_report
    validate_report(report)
    (output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    from build_static_site import FILES
    allowed=FILES
    actual={p.name for p in output.iterdir()};assert actual==allowed,'Unexpected files in publication directory'
    keys=[v.encode() for k,v in dotenv_values(RUNTIME.parent/'private'/'.env').items() if 'KEY' in k and v]
    for p in output.iterdir():
        data=p.read_bytes();assert not any(key in data for key in keys),'Credential in publication bundle'
        assert not re.search(rb'sk-(?:lf-)?[A-Za-z0-9_-]{20,}|[A-Z]:[\\/](?:Users|Agent_Related)[\\/]',data),'Private value in publication bundle'
    print(json.dumps({'files':len(actual),'bytes':sum(p.stat().st_size for p in output.iterdir()),'episodes':len(cases),'credential_matches':0,'backend_included':False}))

if __name__=='__main__':main()
