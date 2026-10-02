"""Executable script/table alternative for the same task and revision contract."""
import asyncio
import csv
import json
from adoptlab.config import RUNTIME
from adoptlab.store import Store
from adoptlab.engine import execute,reverify
from adoptlab.tasks import MATERIALS

async def main():
    store=Store(RUNTIME.parent/'comparison-baseline'/'v03');exp=store.experiment('Script and table reference');rows=[]
    for tid in ['task-01','task-11']:
        for variant in ['A','B']:
            r=await execute(store,store.queue(exp,tid,variant))
            rows.append({'run_id':r['id'],'task':tid,'material':variant,'passed':reverify(store,r['id'])['verification']['passed'],'seconds':r['result']['elapsed_seconds'],'requests':r['result']['requests']})
    old=rows[0]['run_id'];feedback=store.feedback(exp,old,'Explain the verifier and both output files.')
    revised=store.add_material(MATERIALS['B']['guide']+' Inspect result.json and summary.json with independent verification.',MATERIALS['B']['descriptions'],name='Script reference revision',parent='A',reason='Clarify acceptance')
    r=await execute(store,store.queue(exp,'task-01',revised['id']));revision=store.revision(feedback,r['id'],'Changed material, comparable task and accepted artifacts.')
    with (store.root/'results.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
    (store.root/'summary.json').write_text(json.dumps({'rows':rows,'revision_id':revision,'retest_run':r['id'],'source':'automated_script_reference','human_participants':0},indent=2),encoding='utf-8')
    print(json.dumps({'checks':len(rows),'passed':all(r['passed'] for r in rows),'revision_verified':bool(revision)}))

if __name__=='__main__':asyncio.run(main())
