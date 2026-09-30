"""Create an allowlisted static publication bundle, without backend or credentials."""
import json
import re
import shutil
from pathlib import Path
from dotenv import dotenv_values
from adoptlab.config import CODE,RUNTIME
from adoptlab.store import Store
from adoptlab.tasks import MATERIALS,catalog

def main():
    output=RUNTIME.parent/'publication'/'adoptlab-site';output.mkdir(parents=True,exist_ok=True)
    source=CODE/'public-site'
    for name in ['index.html','site.css','site.js','_headers']:shutil.copy2(source/name,output/name)
    for name in ['tutorial.md','experiment-results.md','competitive.md']:shutil.copy2(CODE/'docs'/name,output/name)
    shutil.copy2(CODE/'LICENSE',output/'LICENSE.txt')
    s=Store();e=next(e for e in s.experiments() if e['title']=='Frozen exploratory matrix v1')
    cases=[]
    for r in s.runs(e['id']):
        v=r['result']['verification'];cases.append({'task_id':r['task_id'],'family':catalog()[r['task_id']]['family'],
            'material':r['material'],'trial':r['trial'],'passed':r['status']=='succeeded' and v['passed'],
            'kind':v['kind'],'reason':v['reason'],'cost_upper_cny':r['result']['cost_upper_cny']})
    report={'schema':'adoptlab-static-evidence-v1','recorded_date':'2026-09-30','model':'deepseek-flash','materials':MATERIALS,'cases':cases,
            'limitations':'One model, synthetic records, correlated repeats and bundled guide/description changes. This is a recorded explorer, with no live inference or unique-user claim.'}
    (output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    allowed={'index.html','site.css','site.js','_headers','report.json','tutorial.md','experiment-results.md','competitive.md','LICENSE.txt'}
    actual={p.name for p in output.iterdir()};assert actual==allowed,'Unexpected files in publication directory'
    keys=[v.encode() for k,v in dotenv_values(RUNTIME.parent/'private'/'.env').items() if 'KEY' in k and v]
    for p in output.iterdir():
        data=p.read_bytes();assert not any(key in data for key in keys),'Credential in publication bundle'
        assert not re.search(rb'sk-(?:lf-)?[A-Za-z0-9_-]{20,}|[A-Z]:[\\/](?:Users|Agent_Related)[\\/]',data),'Private value in publication bundle'
    print(json.dumps({'files':len(actual),'bytes':sum(p.stat().st_size for p in output.iterdir()),'episodes':len(cases),'credential_matches':0,'backend_included':False}))

if __name__=='__main__':main()
