"""One bounded first task; the existing engine and oracle own execution truth."""
import json
from .engine import execute, reverify

TASK='task-01'
MATERIAL='B'

async def first_task(store):
    experiment=store.experiment('First verified task')
    run_id=store.queue(experiment,TASK,MATERIAL,'protocol',cohort='automation')
    run=await execute(store,run_id)
    verification=reverify(store,run_id) if run['result'] else None
    passed=bool(run['status']=='succeeded' and verification and verification['verification']['passed'] and all(verification[k] for k in ['artifact_hash_matches','manifest_matches_db','task_matches']))
    summary={'schema':'adoptlab-first-task-v1','passed':passed,'experiment_id':experiment,'run_id':run_id,
             'task_id':TASK,'material':MATERIAL,'mode':'protocol','status':run['status'],
             'verification':verification,'requests':run['result']['requests'] if run['result'] else 0,
             'next_action':'Open the developer page to inspect outputs and save feedback.' if passed else 'Inspect the failed contract checks, run doctor --target builtin, then start a new task explicitly.'}
    (store.root/(experiment+'.report.json')).write_text(json.dumps(store.export(experiment),indent=2),encoding='utf-8')
    (store.root/(run_id+'.first-task.json')).write_text(json.dumps(summary,indent=2),encoding='utf-8')
    return summary
