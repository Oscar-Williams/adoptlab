"""Promptfoo custom Python provider: the same bounded executor and oracle."""
import asyncio
import json
from adoptlab.store import Store
from adoptlab.engine import execute,reverify

def call_api(prompt, options, context):
    config=options.get('config',{})
    store=Store()
    exp=store.experiment('Promptfoo same-task experience')
    material=str(context.get('vars',{}).get('material','A'))
    task=str(context.get('vars',{}).get('task','task-01'))
    mode=config.get('mode','protocol')
    run=store.queue(exp,task,material,mode)
    result=asyncio.run(execute(store,run))
    if result['status']=='queued':return {'error':'Shared runner is busy; finish active experiment before comparison.'}
    if context.get('vars',{}).get('fault'):
        out=store.root/'runs'/run/'outputs'/'summary.json'
        out.write_text('{"count":999,"totals_cents":{}}',encoding='utf-8')
    verification=reverify(store,run)['verification']
    return {'output':json.dumps({'run_id':run,'experiment_id':exp,'material':material,'task_id':task,'passed':verification['passed'],
                'verification':verification,'cost_upper_cny':result['result']['cost_upper_cny'],'mode':mode})}
