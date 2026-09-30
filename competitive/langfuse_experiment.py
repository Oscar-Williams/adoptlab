"""Cloud submission is gated on user-owned Langfuse project credentials."""
import asyncio
import os
import json
from adoptlab.config import load_credentials
from adoptlab.engine import execute
from adoptlab.store import Store
from adoptlab.tracing import client,Recorder

active_client=None

async def task(*,item,**kwargs):
    store=Store();exp=store.experiment('Langfuse same-task experience')
    inp=item['input']
    run=store.queue(exp,inp['task'],'B' if inp.get('material')=='B' else 'A',inp.get('mode','protocol'))
    result=await execute(store,run,Recorder(active_client) if active_client else None)
    if not result['result']:return {'passed':False,'verification':{'reason':'runner_busy'},'cost_upper_cny':0,'run_id':run}
    if active_client:
        trace_id=active_client.get_current_trace_id()
        (store.root/'last-langfuse-trace.json').write_text(json.dumps({'trace_id':trace_id,'url':None}),encoding='utf-8')
    return {'passed':result['result']['verification']['passed'],'verification':result['result']['verification'],
            'cost_upper_cny':result['result']['cost_upper_cny'],'run_id':run}

def evaluator(*,output,**kwargs):
    from langfuse import Evaluation
    return Evaluation(name='independent_contract',value=float(output['passed']))

def main():
    global active_client
    load_credentials()
    if not all(os.getenv(k) for k in ['LANGFUSE_PUBLIC_KEY','LANGFUSE_SECRET_KEY']):
        print(json.dumps({'status':'awaiting_user_project_credentials','uploaded':False}));return
    active_client=client()
    # Task items contain no expected artifacts or personal data.
    result=active_client.run_experiment(name='AdoptLab materials comparison',data=[{'input':{'task':t,'material':v,'mode':'model'}} for t in ['task-01','task-11'] for v in ['A','B']],task=task,evaluators=[evaluator],max_concurrency=1)
    active_client.flush()
    path=Store().root/'last-langfuse-trace.json'
    if path.exists():
        trace=json.loads(path.read_text(encoding='utf-8'))
        try:trace['url']=active_client.get_trace_url(trace_id=trace['trace_id'])
        except Exception:pass
        path.write_text(json.dumps(trace),encoding='utf-8')
    print(result.format())

if __name__=='__main__':main()
