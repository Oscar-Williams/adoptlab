"""Reproducible local protocol cases; never counted as human adoption."""
import asyncio
import json
import sqlite3
import os
import subprocess
from pathlib import Path
import httpx

BASE=os.getenv('ADOPTLAB_VALIDATION_URL','http://127.0.0.1:8780')
ROOT=Path(__file__).resolve().parents[1]

async def main():
    # Only copy the already-pinned public profile, never historical runs or credentials.
    from adoptlab.config import RUNTIME
    from adoptlab.store import Store
    s=Store(RUNTIME)
    profile_id=os.getenv('ADOPTLAB_VALIDATION_PROFILE','filesystem-v04')
    suffix=os.getenv('ADOPTLAB_VALIDATION_TASK_SUFFIX','v04')
    image=subprocess.check_output(['docker','image','inspect',os.getenv('ADOPTLAB_VALIDATION_IMAGE','adoptlab-filesystem:v04'),'--format','{{.Id}}'],text=True).strip()
    profile={'id':profile_id,'image':image,'version':'f46d9578190b476b3501923ea8977d899e8db2cb','argv':['/input','/output'],'tools':['read_text_file','write_file'],'memory_mb':256,'cpus':1,'pids':64}
    s.register('profile',profile)
    task=json.loads((ROOT/'examples/filesystem-task.json').read_text())
    task.update(id='docs-evidence-'+suffix,profile=profile_id)
    config={**task,'id':'docs-config-'+suffix,'family':'document-config','instruction':'Read /input/config-guide.txt. Save endpoint, retry_limit and citation_line in /output/config.json. citation_line is the one-based line containing the endpoint.','fixtures':{'config-guide.txt':'Service reference\nEndpoint: /v2/search\nRetry limit: 3\n'},'steps':[{'tool':'read_text_file','arguments':{'path':'/input/config-guide.txt'}},{'tool':'write_file','arguments':{'path':'/output/config.json','content':'{"endpoint":"/v2/search","retry_limit":3,"citation_line":2}'}}],'rules':[{'file':'config.json','op':'equals','path':['endpoint'],'expected':'/v2/search'},{'file':'config.json','op':'equals','path':['retry_limit'],'expected':3},{'file':'config.json','op':'equals','path':['citation_line'],'expected':2}]}
    (ROOT/'examples/document-config-task.json').write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8')
    async with httpx.AsyncClient(base_url=BASE,timeout=240,trust_env=False) as c:
        async def post(path,data):
            r=await c.post(path,json=data);r.raise_for_status();return r.json()
        for t in [task,config]:
            assert (await post('/api/tasks/preflight',t))['valid']
            await post('/api/tasks/import',t)
        material=await post('/api/materials',{'name':'Filesystem baseline','guide':'Read input documents; write the requested JSON to /output.','descriptions':{'read_text_file':'Read UTF-8 text using an absolute path under /input.','write_file':'Write UTF-8 content with path and content under /output.'}})
        revised=await post('/api/materials',{'name':'Filesystem explicit evidence','parent':material['id'],'reason':'Clarify independent field and citation acceptance.','guide':'Read input documents. Write the required JSON artifact to /output. Preserve exact values and a source citation or one-based citation_line as requested.','descriptions':material['content']['descriptions']})
        builtin=s.material('B')
        br=await post('/api/materials',{'name':'Records explicit artifact','parent':'B','reason':'Explicit output and verification handoff.','guide':builtin['content']['guide']+' Always save the required artifact before finishing.','descriptions':builtin['content']['descriptions']})
        exp=(await post('/api/experiments',{'title':'v0.4 independent three-case protocol validation'}))['id']
        cases=[]
        for tid,old,new in [('task-01','B',br['id']),(task['id'],material['id'],revised['id']),(config['id'],material['id'],revised['id'])]:
            runs=[]
            for mid in [old,new]:
                r=await post('/api/experiments/'+exp+'/batch',{'tasks':[tid],'materials':[mid],'mode':'protocol','trials':1})
                rid=r['run_ids'][0];deadline=asyncio.get_running_loop().time()+210
                while True:
                    run=(await c.get('/api/runs/'+rid)).json()
                    if run['status'] not in ['queued','running']:break
                    assert asyncio.get_running_loop().time()<deadline,'RUN_TIMEOUT'
                    await asyncio.sleep(.3)
                assert run['status']=='succeeded',run
                runs.append(run)
            f=await post('/api/feedback',{'experiment_id':exp,'run_id':runs[0]['id'],'text':'Protocol output passes. Clarify guide evidence requirements; this does not establish a model benefit.'})
            rev=await post('/api/revisions',{'feedback_id':f['id'],'new_run':runs[1]['id'],'decision':'Same-condition protocol retest passed. Model effect and user benefit remain unknown.'})
            gate=await post('/api/releases',{'experiment_id':exp,'material':new,'tasks':[tid],'mode':'protocol'})
            assert gate['verdict']=='passed',gate
            cases.append({'task_id':tid,'old_run':runs[0]['id'],'new_run':runs[1]['id'],'revision':rev['id'],'release':gate,'scope':'protocol only'})
        report=(await c.get('/api/experiments/'+exp+'/export')).json()
        (ROOT/'runtime/v04-validation.json').write_text(json.dumps({'experiment_id':exp,'cases':cases,'report':report},indent=2),encoding='utf-8')
        sanitized={'schema':'adoptlab-upgrade-evidence-v1','mode':'protocol','human_sessions':0,'cases':[],'limitations':['Protocol checks do not establish model improvement or human adoption.','Historical experiment denominators remain in report.json.']}
        for case in cases:
            runs=[]
            for rid in [case['old_run'],case['new_run']]:
                r=s.get_run(rid);v=r['result'];p=v['provenance']
                runs.append({'id':rid,'status':r['status'],'passed':v['verification']['passed'],'condition':s.condition(r),'task_hash':p['task_hash'],'material_hash':p['material_hash'],'artifact_hash':v['verification']['artifact_hash'],'mode':r['mode'],'cohort':r['cohort']})
            sanitized['cases'].append({'task_id':case['task_id'],'runs':runs,'release':{k:case['release'][k] for k in ['verdict','comparable']}})
        (ROOT/'public-site/workbench-evidence.json').write_text(json.dumps(sanitized,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'experiment_id':exp,'cases':len(cases),'accepted_runs':6,'mode':'protocol','human_sessions':0}))

if __name__=='__main__':asyncio.run(main())
