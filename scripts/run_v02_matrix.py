"""Freeze and run the guide x description factorial on the existing task families."""
import asyncio
import json
from adoptlab.store import Store
from adoptlab.engine import execute
from adoptlab.tasks import MATERIALS,catalog
from adoptlab.config import digest

def main():
    s=Store();path=s.root/'v02-factorial-protocol.json'
    if path.exists():protocol=json.loads(path.read_text(encoding='utf-8'))
    else:
        variants={}
        for guide in ['A','B']:
            for desc in ['A','B']:
                key=guide+desc
                variants[key]=s.add_material(MATERIALS[guide]['guide'],MATERIALS[desc]['descriptions'],name='Guide '+guide+' / descriptions '+desc,reason='Frozen 2x2 factorial; backend and tool schemas retained.')['id']
        exp=s.experiment('v0.2 guide x descriptions factorial')
        protocol={'schema':'adoptlab-factorial-v1','experiment_id':exp,'tasks':list(catalog()),'catalog_hash':digest(catalog()),'variants':variants,'trials':3,'split_policy':'Family-level exploration and holdout assignments from frozen catalogue. No post-result tuning.','interpretation':'Exploratory synthetic repeated-task evidence; six correlated families, one model. Guide and description interaction evaluated without user-adoption claims.'}
        path.write_text(json.dumps(protocol,indent=2),encoding='utf-8')
    assert protocol['catalog_hash']==digest(catalog()),'Frozen task catalogue changed'
    exp=protocol['experiment_id'];existing={(r['task_id'],r['material'],r['trial'],r['mode']) for r in s.runs(exp)}
    for mode in ['protocol','model']:
        trials=1 if mode=='protocol' else protocol['trials']
        for trial in range(1,trials+1):
            for ti,task in enumerate(protocol['tasks']):
                variants=list(protocol['variants'].items());offset=(ti+trial)%4;variants=variants[offset:]+variants[:offset]
                for key,material in variants:
                    if (task,material,trial,mode) in existing:continue
                    id=s.queue(exp,task,material,mode,trial=trial);r=asyncio.run(execute(s,id))
                    print(json.dumps({'variant':key,'task':task,'trial':trial,'mode':mode,'status':r['status'],'cost':(r['result'] or {}).get('cost_upper_cny',0)}),flush=True)
                    if not r['result'] or r['result'].get('error_code') in {'credentials_missing','model_http_401','model_http_402','unpriced_model','BUDGET_EXHAUSTED'}:
                        print(json.dumps({'gate':True,'run_id':id}));return
    report=s.export(exp);report['protocol']=protocol;report['schema']='adoptlab-factorial-report-v2'
    (s.root/'v02-factorial-results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'complete':True,'experiment_id':exp,'runs':len(report['runs'])}))

if __name__=='__main__':main()
