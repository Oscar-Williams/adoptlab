"""Executable role-based review probes. All eight roles are Codex simulations."""
import asyncio
import json
from pathlib import Path
from adoptlab.config import RUNTIME
from adoptlab.store import Store
from adoptlab.engine import execute, reverify

ROLES=[('M1','AI API maintainer','task-01','execution conditions and feedback handoff'),
       ('M2','MCP tool maintainer','docs-evidence-01','container registration and independent acceptance'),
       ('M3','Documentation owner','task-07','material differences and revision evidence'),
       ('D1','New Python/MCP developer','task-01','first protocol task and readable verification'),
       ('D2','Experienced MCP developer','task-05','task contract and reusable problem package'),
       ('D3','Windows developer','task-09','UTF-8 outputs and restored run artifacts'),
       ('D4','Container environment developer','docs-evidence-01','read-only input and output contract'),
       ('D5','English documentation developer','task-11','normal output and correct input rejection')]

async def main():
    source=Store();root=RUNTIME.parent/'release-review';root.mkdir(exist_ok=True)
    results=[]
    for id,role,tid,goal in ROLES:
        s=Store(root/id);mid='B'
        if tid=='docs-evidence-01':
            s.register('profile',source.registered('profile','filesystem-v1'))
            s.register('task',source.task(tid))
            config=json.loads((source.root/'filesystem-run.json').read_text())
            m=source.material(config['materials'][0])['content'];mid=s.add_material(m['guide'],m['descriptions'],name='Review Filesystem')['id']
        exp=s.experiment('Codex simulated '+role)
        first=await execute(s,s.queue(exp,tid,mid,'protocol',cohort='automation',subject='simulation-'+id))
        check=reverify(s,first['id'])
        evidence={'source':'codex_simulation','role':role,'goal':goal,'task_id':tid,'mode':'protocol','initial_status':first['status'],'acceptance':check['verification']['passed'],'run_id':first['id'],'assistance':'Codex executed the documented path; no independent human observation','human_participants':0}
        if id.startswith('M'):
            old=s.material(mid)['content'];feedback=s.feedback(exp,first['id'],'Clarify source paths and independent acceptance for '+role)
            new=s.add_material(old['guide']+' Review both outputs against the independent task contract.',old['descriptions'],name=id+' clarified guide',parent=mid,reason='Simulated review of acceptance explanation')
            second=await execute(s,s.queue(exp,tid,new['id'],'protocol',cohort='automation',subject='simulation-'+id))
            revision=s.revision(feedback,second['id'],'Clarify guidance; same task/backend and independent acceptance retained.')
            evidence.update(revision_id=revision,retest_status=second['status'],changed_material=True,handoff_records=len(s.handoff(exp)['revisions']))
        evidence['problem_export_schema']=s.export(exp)['schema']
        results.append(evidence)
        print(json.dumps({'role':id,'passed':evidence['acceptance'],'retest':evidence.get('retest_status'),'source':'codex_simulation'}),flush=True)
    report={'source':'codex_simulation','simulated_roles':8,'human_participants':0,'observed_human_sessions':0,'records':results,'passed':all(r['acceptance'] for r in results)}
    (root/'review.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    if not report['passed']:raise SystemExit(1)

if __name__=='__main__':asyncio.run(main())
